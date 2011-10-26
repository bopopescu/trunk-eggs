"""
Utilities to make Zope2 a friendlier place.

"""

import datetime
import sys
import urllib

from AccessControl import ClassSecurityInfo, Unauthorized
from AccessControl.Permission import Permission
from Acquisition import Implicit, aq_base
from OFS.interfaces import IItem, IObjectManager, IApplication
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from Globals import DTMLFile
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from DateTime import DateTime
import simplejson as json
from decimal import Decimal
from dateutil.parser import parse
from Products.Naaya.interfaces import IObjectView
from naaya.core.utils import force_to_unicode, is_valid_email
from naaya.core.utils import unescape_html_entities
from naaya.core.utils import icon_for_content_type
from Products.Naaya.interfaces import INySite
from backport import any

def redirect_to(tmpl):
    """
    Generate a simple view that redirects to the specified URL.

    For example, this declaration:
    >>> the_old_page = redirect_to('%(self_url)s/the_new_page')

    is equivalent with:
    >>> def the_new_page(self, REQUEST):
    >>>     ''' perform redirect '''
    >>>     REQUEST.RESPONSE.redirect(self.absolute_url() + '/the_new_page')

    """
    def redirect(self, REQUEST):
        """ automatic redirect """
        url = tmpl % {
            'self_url': self.absolute_url(),
        }
        REQUEST.RESPONSE.redirect(url)
    return redirect

def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    else:
        raise ValueError('Can not encode value %r' % value)

class RestrictedToolkit(SimpleItem):
    """
    RestrictedToolkit exposes some useful methods to RestrictedPython
    code (e.g. Scripts in ZODB, PageTemplates). You can get a hold of
    the RestrictedPython instance (it's a singleton) easily:

      >>> rstk = self.rstk

    It's pulled form the NySite object via acquisition.
    """
    security = ClassSecurityInfo()
    # by default, all methods are "public"

    _button_form = PageTemplateFile('zpt/button_form.zpt', globals())
    def button_form(self, **kwargs):
        """
        A simple one-button form, useful when a button that does POST
        is more appropriate than a link that does GET.

        It takes a few keyword arguments.
        `label`: what text should appear on the button;
        `button_title`: tooltip text for the button;
        `action`: what should the form do (e.g. ``"POST"``);
        `formdata`: dictionary of name/value pairs to be embedded as
        hidden inputs in the form.

        None of the fields are translated by default; it's your
        responsability to do that before calling ``button_form``.
        """
        return self._button_form(**kwargs)

    def parse_string_to_datetime(self, date_string):
        """
        Parse a date/time string to a Python ``datetime.datetime``
        object.
        """
        return parse(date_string)

    def convert_datetime_to_DateTime(self, dt):
        """
        Convert a Python ``datetime.datetime`` object to a
        Zope2 ``DateTime``.
        """
        return dt2DT(dt)

    def convert_DateTime_to_datetime(self, DT):
        """
        Convert a Zope2 ``DateTime object`` to a Python
        ``datetime.datetime``.
        """
        return DT2dt(DT)

    def DT_strftime_rfc3339(self, date):
        """
        Convert a Zope DateTime value to rfc-3339 format, suitable for use
        in an Atom feed.
        """
        d = DT2dt(date).strftime('%Y-%m-%dT%H:%M:%S%z')
        return d[:-2] + ':' + d[-2:]

    def dt_strftime(self, date, format):
        """
        Convert a Zope DateTime value to rfc-3339 format, suitable for use
        in an Atom feed.
        """
        return datetime.datetime.strftime(date, format)

    def json_dumps(self, obj):
        """
        Convert a Python object to JSON
        """
        return json.dumps(obj, default=json_default)

    def json_loads(self, json_data):
        """
        Convert JSON data to a Python object
        """
        return json.loads(json_data)

    def is_descendant_of(self, obj, ancestor):
        """
        Return if the `obj` is somewhere inside `ancestor`
        """
        return is_descendant_of(obj, ancestor)

    def path_in_site(self, obj):
        """ Return path relative to site root """
        return path_in_site(obj)

    def is_valid_email(self, email_str):
        """ Check validity of email address """
        return is_valid_email(email_str)

    def we_provide(self, feature):
        """ Check if the instance provides certain features """
        if feature == 'Excel export':
            try:
                from xlwt import Workbook
                return True
            except ImportError:
                pass
        return False

    def catch_unauthorized(self):
        """
        useful in try..except handlers, like `tal:on-error`::

            <p tal:content="here/read_value"
               on-error="here/rstk/catch_unauthorized"/>
        """
        if sys.exc_info()[0] is Unauthorized:
            return None
        else:
            raise

    def url_quote(self, value):
        """ URL-quote the given value. """
        return urllib.quote(value)

    def unescape_html_entities(self, text):
        """ unescape html entities from the given text """
        return unescape_html_entities(text)

    def simple_paginate(self, items, per_page=4):
        """
        A very simple paginator::

            >>> self.rstk.simple_paginate([1, 2, 3, 4, 5, 6], per_page=4)
            [[1, 2, 3, 4], [5, 6]]
        """
        return simple_paginate(items, per_page)

    def get_object_view_info(self, ob):
        """
        Get object icon, meta_label, and other information, useful when
        displaying the object in a list (e.g. folder index, search results,
        latest news). Behind the scenes, data comes from adapters to the
        :class:`~Products.Naaya.interfaces.IObjectView` interface.
        Currently returns the following fields:

        `icon`
            the return value from
            :func:`~Products.Naaya.interfaces.IObjectView.get_icon`
        """

        view_adapter = get_site_manager(ob).getAdapter(ob, IObjectView)

        # Ideally we would just return the adapter, but RestrictedPython blocks
        # all access to its methods.
        return {
            'icon': view_adapter.get_icon(),
            # TODO add other fields as needed
        }

    def icon_for_content_type(self, *args, **kwargs):
        """
        Return a dictionary with the url an title of the icon
        for the passed content_type
        """
        return icon_for_content_type(*args, **kwargs)

    def google_analytics(self, ga_id=''):
        """
        Renders Google Analytics form template using the provided
        `ga_id` Analytics Website property ID (UA-number).

        """
        if ga_id == '':
            # No website ID provided; e.g. not configured in portal_statistics
            return ''

        if self.REQUEST.AUTHENTICATED_USER.has_role('Manager'):
            # no google analytics for managers
            return ''

        site = self.getSite()
        forms_tool = site.getFormsTool()
        ga_form = forms_tool.getForm("site_googleanalytics")

        return ga_form.__of__(site)(ga_id=ga_id)

InitializeClass(RestrictedToolkit)


class CaptureTraverse(Implicit):
    """
    Capture any request path and invoke a callback.

    CaptureTraverse is useful when we need to capture arbitrary request
    paths. If our object is published at `http://example.com/my/object`,
    and we expect requests at `http://example.com/my/object/magic/a/b/c`,
    then we can use CaptureTraverse like so::

      >>> def handle_magic(context, path, REQUEST):
      ...     return ('the page! path=%r, url=%r' %
                      (path, context.absolute_url()))
      >>> class MyObject(SimpleItem):
      ...     # implementation of MyObject
      ...     # ...
      ...
      ...     magic = CaptureTraverse(handle_magic)

    GET requests for `http://example.com/my/object/magic/a/b/c` will
    receive the following response::

      the page! path=('a', 'b', 'c'), url='http://example.com/my/object'

    """

    security = ClassSecurityInfo()

    def __init__(self, callback, path=tuple(), context=None):
        self.callback = callback
        self.path = path
        self.context = context

    def __bobo_traverse__(self, REQUEST, name):
        new_path = self.path + (name,)
        context = self.context or (self.aq_parent,)
        return CaptureTraverse(self.callback, new_path, context).__of__(self)

    def __call__(self, REQUEST):
        assert self.path[-1] == 'index_html'
        return self.callback(self.context[0], self.path[:-1], REQUEST)


##################################################################
### `UnnamedTimeZone`, `dt2DT` and `DT2dt` come from Plone's
### Products.ATContentTypes.utils

class UnnamedTimeZone(datetime.tzinfo):
    """Unnamed timezone info"""

    def __init__(self, minutes):
        self.minutes = minutes

    def utcoffset(self, dt):
        return datetime.timedelta(minutes=self.minutes)

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        aheadUTC = self.minutes > 0
        if aheadUTC:
            sign = '+'
            mins = self.minutes * -1
        else:
            sign = '-'
            mins = self.minutes
        wholehours = int(self.minutes / 60.)
        minutesleft = self.minutes % 60
        return """%s%0.2d%0.2d""" % (sign, wholehours, minutesleft)

def dt2DT(date):
    """ Convert Python's datetime to Zope's DateTime """
    args = (date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond, date.tzinfo)
    timezone = args[7].utcoffset(date)
    secs = timezone.seconds
    days = timezone.days
    hours = secs/3600 + days*24
    mod = "+"
    if hours < 0:
        mod = ""
    timezone = "GMT%s%d" % (mod, hours)
    args = list(args[:6])
    args.append(timezone)
    return DateTime(*args)

def DT2dt(date):
    """ Convert Zope's DateTime to Pythons's datetime """
    # seconds (parts[6]) is a float, so we map to int
    args = map(int, date.parts()[:6])
    args.append(0)
    args.append(UnnamedTimeZone(int(date.tzoffset()/60)))
    return datetime.datetime(*args)

def ensure_tzinfo(dt, default_tz=UnnamedTimeZone(0)):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=default_tz)
    else:
        return dt

folder_manage_main_plus = DTMLFile('zpt/folder_main_plus', globals())
"""
The OFS.ObjectManager `manage_main` template, modified to render two
extra pieces of content: ``ny_before_listing`` and ``ny_after_listing``.
"""

def exorcize_local_properties(obj):
    """
    remove any data set by LocalPropertyManager, recover plain
    (non-localized) string values, and set them as simple properties.

    Returns `None` if nothing was touched, or a list of extracted
    property names (which may be empty if we only removed empty
    LocalPropertyManager data structures).
    """

    obj.getId() # make sure it's loaded from zodb
    changed = False

    names = []
    default_lang = obj.__dict__.get('_default_lang', 'en')
    if '_local_properties' in obj.__dict__:
        for name, localdata in obj.__dict__['_local_properties'].items():
            if default_lang in localdata:
                value = localdata[default_lang][0]
            else:
                value = localdata.values()[0][0]
            obj.__dict__[name] = force_to_unicode(value)
            changed = True
            names.append(name)

    for attrname in ['_default_language', '_languages', '_local_properties',
                     '_local_properties_metadata']:
        if attrname in obj.__dict__:
            del obj.__dict__[attrname]
            changed = True

    if changed:
        obj._p_changed = True
        return names
    else:
        return None

def abort_transaction_keep_session(request):
    """
    We need to abort the transaction (e.g. an object was created but the
    add form generated errors). We preserve whatever data has been set on
    the session.
    """
    session = dict(request.SESSION)
    import transaction; transaction.abort()
    request.SESSION.update(session)

def permission_add_role(context, permission, role):
    """ Adds a role to a permission"""
    p = Permission(permission, (), context)
    crt_roles = p.getRoles()
    ty = type(crt_roles)
    p.setRoles(ty(set(crt_roles) | set([role])))

def physical_path(ob):
    # TODO deprecate and replace with ofs_path
    return '/'.join(ob.getPhysicalPath())

def relative_object_path(obj, ancestor):
    """
    Compute the relative path from `ancestor` to `obj` (`obj` must be
    somewhere inside `ancestor`)
    """

    ancestor_path = '/'.join(ancestor.getPhysicalPath())
    obj_path = '/'.join(obj.getPhysicalPath())

    if not obj_path.startswith(ancestor_path):
        raise ValueError('My path is not in the site. Panicking.')
    return obj_path[len(ancestor_path)+1:]

def ofs_path(obj):
    """
    Return a string representation of an object's path, e.g.
    ``/mysite/about/info``
    """
    return '/'.join(obj.getPhysicalPath())

def is_descendant_of(obj, ancestor):
    """
    Return if the `obj` is somewhere inside `ancestor`
    """
    # add '/' to make sure last ids are compared correctly
    ancestor_path = ofs_path(ancestor) + '/'
    obj_path = ofs_path(obj) + '/'
    return obj_path.startswith(ancestor_path)

def path_in_site(obj):
    """
    Compute the relative path of `obj` in reference to its
    containing site
    """
    return relative_object_path(obj, obj.getSite())

def ofs_walk(top, filter=[IItem], containers=[IObjectManager]):
    """
    Walk the Zope object graph and yield the objects it finds.

    :param top: Object where the walk starts. Regardless of `filter` and
        `containers`, `top` is never yielded, but always walked.
    :param filter: Filter yielded objects. An object will be yielded only if
        it provides one of the specified interfaces.
    :param containers: Choose which container objects are walked.
        :func:`ofs_walk` will call itself recursively if an object implements
        one of the specified interfaces.
    """

    if not hasattr(aq_base(top), 'objectValues'):
        raise ValueError("Object %r does not have sub-objects" % top)

    for ob in top.objectValues():
        if any(i.providedBy(ob) for i in filter):
            yield ob

        if any(i.providedBy(ob) for i in containers):
            for item in ofs_walk(ob, filter, containers):
                yield item

def simple_paginate(items, per_page=4):
    output = []
    for offset in xrange(0, len(items), per_page):
        output.append(items[offset:offset+per_page])
    return output

def get_site_manager(context):
    """
    Return the site manager for a given object. It will typically return the
    local site manager of the object's site.
    """
    return context.getSite().getSiteManager()
