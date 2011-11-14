# The contents of this file are subject to the Mozilla Public
# License Version 1.1 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS
# IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
# implied. See the License for the specific language governing
# rights and limitations under the License.
#
# The Initial Owner of the Original Code is European Environment
# Agency (EEA).  Portions created by Finsiel Romania and Eau de Web are
# Copyright (C) European Environment Agency.  All
# Rights Reserved.
#
# Authors:
#
# Cornel Nitu, Eau de Web
# Dragos Chirila

#Python imports
from copy import deepcopy
import os
import sys

#Zope imports
from Globals import InitializeClass
from App.ImageFile import ImageFile
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import Products

#Product imports
from naaya.content.base.constants import *
from Products.NaayaBase.constants import *
from Products.NaayaBase.NyContainer import NyContainer
from Products.NaayaBase.NyAttributes import NyAttributes
from Products.NaayaBase.NyValidation import NyValidation
from Products.NaayaBase.NyCheckControl import NyCheckControl
from study_item import study_item
from converters.xslt import Converter
from permissions import PERMISSION_ADD_STUDY

#module constants
METATYPE_OBJECT = 'Naaya Study'
LABEL_OBJECT = 'Study'
OBJECT_FORMS = ['study_add', 'study_edit', 'study_index', 'study_style']
OBJECT_CONSTRUCTORS = ['manage_addNyStudy_html', 'study_add', 'addNyStudy', 'importNyStudy']
OBJECT_ADD_FORM = 'study_add'
DESCRIPTION_OBJECT = 'This is Naaya Study type.'
PREFIX_OBJECT = 'doc'
PROPERTIES_OBJECT = {
    'id':           (0, '', ''),
    'title':        (1, MUST_BE_NONEMPTY, 'The Title field must have a value.'),
    'description':  (0, '', ''),
    'coverage':     (0, '', ''),
    'keywords':     (0, '', ''),
    'sortorder':    (0, MUST_BE_POSITIV_INT, 'The Sort order field must contain a positive integer.'),
    'releasedate':  (0, MUST_BE_DATETIME, 'The Release date field must contain a valid date.'),
    'discussion':   (0, '', ''),
    'body':         (0, '', ''),
    'toc':          (0, '', ''),
    'topic':        (0, '', ''),
    'scope':        (0, '', ''),
    'lang':         (0, '', '')
}

# this dictionary is updated at the end of the module
config = {
        'product': 'NaayaContent',
        'module': 'NyStudy',
        'package_path': os.path.abspath(os.path.dirname(__file__)),
        'meta_type': 'Naaya Study',
        'label': 'Study',
        'permission': PERMISSION_ADD_STUDY,
        'forms': ['study_add', 'study_edit', 'study_index', 'study_style'],
        'add_form': 'study_add',
        'description': 'This is Naaya Study type.',
        'properties': PROPERTIES_OBJECT,
        'default_schema': None,
        'schema_name': 'NyStudy',
        'import_string': 'importNyStudy',
        '_module': sys.modules[__name__],
        'additional_style': None,
        'icon': os.path.join(os.path.dirname(__file__), 'www', 'NyStudy.gif'),
        '_misc': {
                'NyStudy.gif': ImageFile('www/NyStudy.gif', globals()),
                'NyStudy_marked.gif': ImageFile('www/NyStudy_marked.gif', globals()),
            },
    }

def study_add(self, REQUEST=None, RESPONSE=None):
    """ """
    id = PREFIX_OBJECT + self.utGenRandomId(6)
    self.addNyStudy(id=id, title='', description='', coverage='', keywords='', sortorder='',
        body='', topic='', scope='', REQUEST=None)
    if REQUEST: REQUEST.RESPONSE.redirect('%s/add_html' % self._getOb(id).absolute_url())

def addNyStudy(self, id='', title='', description='', coverage='', keywords='',
    sortorder='', body='', topic='', scope='', toc='', contributor=None, releasedate='', discussion='',
    lang=None, REQUEST=None, **kwargs):
    """
    Create a Study type og object.
    """
    #process parameters
    id = self.utCleanupId(id)
    if not id: id = self.utGenObjectId(title)
    try: sortorder = abs(int(sortorder))
    except: sortorder = DEFAULT_SORTORDER
    if contributor is None: contributor = self.REQUEST.AUTHENTICATED_USER.getUserName()
    releasedate = self.process_releasedate(releasedate)
    if lang is None: lang = self.gl_get_selected_language()
    #generate table of contents
    if toc:
        toc_body = self._generate_toc(body)
    else:
        toc_body = ''
    #check if the id is invalid (it is already in use)
    i = 0
    while self._getOb(id, None):
        i += 1
        id = '%s-%u' % (id, i)
    #create object
    ob = NyStudy(id, title, description, coverage, keywords, sortorder, body,
        contributor, topic, scope, toc_body, toc, releasedate, lang)
    self.gl_add_languages(ob)
    self._setObject(id, ob)
    #extra settings
    ob = self._getOb(id)
    ob.updatePropertiesFromGlossary(lang)
    if kwargs.has_key('submitted'): ob.submitThis()
    if discussion: ob.open_for_comments()
    self.recatalogNyObject(ob)
    #redirect if case
    if REQUEST is not None:
        if REQUEST.has_key('submitted'): ob.submitThis()
        l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
        if l_referer == 'study_manage_add' or l_referer.find('study_manage_add') != -1:
            return self.manage_main(self, REQUEST, update_menu=1)
        elif l_referer == 'study_add':
            self.setSession('referer', self.absolute_url())
            REQUEST.RESPONSE.redirect('%s/messages_html' % self.absolute_url())

def importNyStudy(self, param, id, attrs, content, properties, discussion, objects):
    #this method is called during the import process
    try: param = abs(int(param))
    except: param = 0
    if param == 3:
        #just try to delete the object
        try: self.manage_delObjects([id])
        except: pass
    else:
        ob = self._getOb(id, None)
        if param in [0, 1] or (param==2 and ob is None):
            if param == 1:
                #delete the object if exists
                try: self.manage_delObjects([id])
                except: pass
            addNyStudy(self, id=id,
                sortorder=attrs['sortorder'].encode('utf-8'),
                contributor=self.utEmptyToNone(attrs['contributor'].encode('utf-8')),
                scope=attrs['scope'].encode('utf-8'),
                topic=attrs['topic'].encode('utf-8'),
                toc=attrs['toc'].encode('utf-8'),
                discussion=abs(int(attrs['discussion'].encode('utf-8'))))
            ob = self._getOb(id)
            for property, langs in properties.items():
                [ ob._setLocalPropValue(property, lang, langs[lang]) for lang in langs if langs[lang]!='' ]
            ob.approveThis(approved=abs(int(attrs['approved'].encode('utf-8'))),
                approved_by=self.utEmptyToNone(attrs['approved_by'].encode('utf-8')))
            if attrs['releasedate'].encode('utf-8') != '':
                ob.setReleaseDate(attrs['releasedate'].encode('utf-8'))
            ob.checkThis(attrs['validation_status'].encode('utf-8'),
                attrs['validation_comment'].encode('utf-8'),
                attrs['validation_by'].encode('utf-8'),
                attrs['validation_date'].encode('utf-8'))
            ob.submitThis()
            ob.import_comments(discussion)
            self.recatalogNyObject(ob)
        for object in objects:
            self.import_data_custom(ob, object)

class NyStudy(NyAttributes, study_item, NyContainer, NyCheckControl, NyValidation):
    """ """

    meta_type = METATYPE_OBJECT
    meta_label = LABEL_OBJECT
    icon = 'misc_/NaayaContent/NyStudy.gif'
    icon_marked = 'misc_/NaayaContent/NyStudy_marked.gif'

    def manage_options(self):
        """ """
        l_options = (NyContainer.manage_options[0],)
        if not self.hasVersion():
            l_options += ({'label': 'Properties', 'action': 'manage_edit_html'},)
        l_options += ({'label': 'View', 'action': 'index_html'},) + NyContainer.manage_options[3:8]
        return l_options

    def all_meta_types(self, interfaces=None):
        """ """
        y = []
        additional_meta_types = ['Image']
        for x in Products.meta_types:
            if x['name'] in additional_meta_types:
                y.append(x)
        return y

    security = ClassSecurityInfo()

    def __init__(self, id, title, description, coverage, keywords, sortorder, body,
        contributor, topic, scope, toc_body, toc, releasedate, lang):
        """ """
        self.id = id
        study_item.__dict__['__init__'](self, title, description, coverage, keywords, sortorder, body, topic, scope, toc_body, toc, releasedate, lang)
        NyValidation.__dict__['__init__'](self)
        NyCheckControl.__dict__['__init__'](self)
        NyContainer.__dict__['__init__'](self)
        self.contributor = contributor

    security.declarePrivate('objectkeywords')
    def objectkeywords(self, lang):
        return u' '.join([self._objectkeywords(lang), self.getLocalProperty('body', lang)])

    security.declarePrivate('export_this_tag_custom')
    def export_this_tag_custom(self):
        return 'topic="%s" scope="%s" validation_status="%s" validation_date="%s" validation_by="%s" validation_comment="%s"' % \
            (self.utXmlEncode(self.topic),
                self.utXmlEncode(self.scope),
                self.utXmlEncode(self.validation_status),
                self.utXmlEncode(self.validation_date),
                self.utXmlEncode(self.validation_by),
                self.utXmlEncode(self.validation_comment))

    security.declarePrivate('export_this_body_custom')
    def export_this_body_custom(self):
        r = []
        ra = r.append
        for l in self.gl_get_languages():
            ra('<body lang="%s"><![CDATA[%s]]></body>' % (l, self.utToUtf8(self.getLocalProperty('body', l))))
        for i in self.getUploadedImages():
            ra('<img param="0" id="%s" content="%s" />' % \
                (self.utXmlEncode(i.id()), self.utXmlEncode(self.utBase64Encode(str(i.data)))))
        return ''.join(r)

    #zmi actions
    security.declareProtected(view_management_screens, 'manageProperties')
    def manageProperties(self, title='', description='', coverage='', keywords='',
        sortorder='', approved='', body='', topic='', scope='', toc='', releasedate='', discussion='', lang='',
        REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        try: sortorder = abs(int(sortorder))
        except: sortorder = DEFAULT_SORTORDER
        if approved: approved = 1
        else: approved = 0
        releasedate = self.process_releasedate(releasedate, self.releasedate)
        if not lang: lang = self.gl_get_selected_language()
        #generate table of contents
        if toc:
            toc_body = self._generate_toc(body)
        else:
            toc_body = ''
        self.save_properties(title, description, coverage, keywords, sortorder, body, topic, scope, toc_body, toc, releasedate, lang)
        self.updatePropertiesFromGlossary(lang)
        if approved != self.approved:
            if approved == 0: approved_by = None
            else: approved_by = self.REQUEST.AUTHENTICATED_USER.getUserName()
            self.approveThis(approved, approved_by)
        self._p_changed = 1
        if discussion: self.open_for_comments()
        else: self.close_for_comments()
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

    security.declareProtected(view_management_screens, 'submitThis')
    def submit_this(self, REQUEST=None):
        """ """
        self.submitThis()
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

    #site actions
    security.declareProtected(PERMISSION_ADD_STUDY, 'process_add')
    def process_add(self, title='', description='', coverage='', keywords='',
        sortorder='', body='', topic='', scope='', toc='', releasedate='', discussion='', lang='', REQUEST=None, **kwargs):
        """ """
        try: sortorder = abs(int(sortorder))
        except: sortorder = DEFAULT_SORTORDER
        #check mandatory fiels
        l_referer = ''
        if REQUEST is not None: l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
        if not(l_referer == 'study_manage_add' or l_referer.find('study_manage_add') != -1):
            r = self.getSite().check_pluggable_item_properties(METATYPE_OBJECT, id=id, title=title, \
                description=description, coverage=coverage, keywords=keywords, sortorder=sortorder, \
                topic=topic, scope=scope, toc=toc, releasedate=releasedate, discussion=discussion, body=body)
        else:
            r = []
        if not len(r):
            if not lang: lang = self.gl_get_selected_language()
            releasedate = self.process_releasedate(releasedate, self.releasedate)
            if self.glCheckPermissionPublishObjects():
                approved, approved_by = 1, self.REQUEST.AUTHENTICATED_USER.getUserName()
            else:
                approved, approved_by = 0, None
            #generate table of contents
            if toc:
                toc_body = self._generate_toc(body)
            else:
                toc_body = ''
            self.save_properties(title, description, coverage, keywords, sortorder, body, topic, scope, toc_body, toc, releasedate, lang)
            self._p_changed = 1
            self.updatePropertiesFromGlossary(lang)
            self.approveThis(approved, approved_by)
            self.submitThis()
            if discussion: self.open_for_comments()
            self.recatalogNyObject(self)
            self.notifyFolderMaintainer(self.getParentNode(), self)
            if REQUEST:
                self.setSession('referer', self.getParentNode().absolute_url())
                REQUEST.RESPONSE.redirect('%s/messages_html' % self.getParentNode().absolute_url())
        else:
            if REQUEST is not None:
                l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
                self.setSessionErrors(r)
                self.set_pluggable_item_session(METATYPE_OBJECT, id=id, title=title, \
                    description=description, coverage=coverage, keywords=keywords, \
                    sortorder=sortorder, topic=topic, scope=scope, releasedate=releasedate, discussion=discussion, body=body, toc=toc, lang=lang)
                REQUEST.RESPONSE.redirect('%s/add_html' % self.absolute_url())
            else:
                raise Exception, '%s' % ', '.join(r)

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'commitVersion')
    def commitVersion(self, REQUEST=None):
        """ """
        if (not self.checkPermissionEditObject()) or (self.checkout_user != self.REQUEST.AUTHENTICATED_USER.getUserName()):
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if not self.hasVersion():
            raise EXCEPTION_NOVERSION, EXCEPTION_NOVERSION_MSG
        self._local_properties_metadata = deepcopy(self.version._local_properties_metadata)
        self._local_properties = deepcopy(self.version._local_properties)
        self.sortorder = self.version.sortorder
        self.releasedate = self.version.releasedate
        self.setProperties(deepcopy(self.version.getProperties()))
        self.checkout = 0
        self.checkout_user = None
        self.version = None
        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('%s/index_html' % self.absolute_url())

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'startVersion')
    def startVersion(self, REQUEST=None):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if self.hasVersion():
            raise EXCEPTION_STARTEDVERSION, EXCEPTION_STARTEDVERSION_MSG
        self.checkout = 1
        self.checkout_user = self.REQUEST.AUTHENTICATED_USER.getUserName()
        self.version = study_item(self.title, self.description, self.coverage, self.keywords, self.sortorder,
            self.body, self.toc, self.releasedate, self.gl_get_selected_language())
        self.version._local_properties_metadata = deepcopy(self._local_properties_metadata)
        self.version._local_properties = deepcopy(self._local_properties)
        self.version.setProperties(deepcopy(self.getProperties()))
        self._p_changed = 1
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('%s/edit_html' % self.absolute_url())

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'saveProperties')
    def saveProperties(self, title='', description='', coverage='', keywords='',
        sortorder='', body='', topic='', scope='', toc='', releasedate='', discussion='', lang=None,
        REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
        if not sortorder: sortorder = DEFAULT_SORTORDER
        if lang is None: lang = self.gl_get_selected_language()
        #check mandatory fiels
        r = self.getSite().check_pluggable_item_properties(METATYPE_OBJECT, title=title, \
            description=description, coverage=coverage, keywords=keywords, sortorder=sortorder, \
            topic=topic, scope=scope, toc=toc, releasedate=releasedate, discussion=discussion, body=body)
        if not len(r):
            sortorder = int(sortorder)
            if not self.hasVersion():
                #this object has not been checked out; save changes directly into the object
                releasedate = self.process_releasedate(releasedate, self.releasedate)
                #generate table of contents
                if toc:
                    toc_body = self._generate_toc(body)
                else:
                    toc_body = ''
                self.save_properties(title, description, coverage, keywords, sortorder, body, topic, scope, toc_body, toc, releasedate, lang)
                self.updatePropertiesFromGlossary(lang)
            else:
                #this object has been checked out; save changes into the version object
                if self.checkout_user != self.REQUEST.AUTHENTICATED_USER.getUserName():
                    raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG
                releasedate = self.process_releasedate(releasedate, self.version.releasedate)
                #generate table of contents
                if toc:
                    toc_body = self._generate_toc(body)
                else:
                    toc_body = ''
                self.version.save_properties(title, description, coverage, keywords, sortorder, body, topic, scope, toc_body, toc, releasedate, lang)
                self.version.updatePropertiesFromGlossary(lang)
            if discussion: self.open_for_comments()
            else: self.close_for_comments()
            self._p_changed = 1
            self.recatalogNyObject(self)
            if REQUEST:
                self.setSessionInfoTrans(MESSAGE_SAVEDCHANGES, date=self.utGetTodayDate())
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), lang))
        else:
            if REQUEST is not None:
                self.setSessionErrors(r)
                self.set_pluggable_item_session(METATYPE_OBJECT, id=id, title=title, \
                    description=description, coverage=coverage, keywords=keywords, \
                    sortorder=sortorder, releasedate=releasedate, discussion=discussion, body=body, topic=topic, scope=scope, toc=toc)
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), lang))
            else:
                raise Exception, '%s' % ', '.join(r)

    security.declarePrivate('_generate_toc')
    def _generate_toc(self, html):
        """ generate table of contents """
        conv = Converter()
        html = html.encode('latin1', 'ignore')
        return unicode(conv("<html>%s</html>" % html, self.style_xsl()), 'utf-8')

    #zmi pages
    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/study_manage_edit', globals())

    #site pages
    security.declareProtected(PERMISSION_ADD_STUDY, 'add_html')
    def add_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'study_add')

    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'study_index')

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'edit_html')
    def edit_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'study_edit')

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'style_xsl')
    def style_xsl(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'study_style')

InitializeClass(NyStudy)

manage_addNyStudy_html = PageTemplateFile('zpt/study_manage_add', globals())
manage_addNyStudy_html.kind = METATYPE_OBJECT
manage_addNyStudy_html.action = 'addNyStudy'
config.update({
    'constructors': (manage_addNyStudy_html, addNyStudy),
    'folder_constructors': [
            # NyFolder.manage_addNyStudy_html = manage_addNyStudy_html
            ('manage_addNyStudy_html', manage_addNyStudy_html),
            ('study_add', study_add),
            ('addNyStudy', addNyStudy),
            (config['import_string'], importNyStudy),
        ],
    'add_method': addNyStudy,
    'validation': issubclass(NyStudy, NyValidation),
    '_class': NyStudy,
})

def get_config():
    return config
