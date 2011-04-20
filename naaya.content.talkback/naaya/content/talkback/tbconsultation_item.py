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
# Agency (EEA).  Portions created by Eau de Web are
# Copyright (C) European Environment Agency.  All
# Rights Reserved.
#
# Authors:
#
# David Batranu, Eau de Web
# Alex Morega, Eau de Web

#Python imports
import os
import sys
import operator

#Zope imports
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Acquisition import Implicit
from App.ImageFile import ImageFile
from OFS.Image import cookId
from AccessControl.Permissions import change_permissions
from DateTime import DateTime

#Product imports
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile
from Products.NaayaCore.managers.utils import utils
from naaya.content.base.constants import *
from Products.NaayaBase.constants import *
from Products.NaayaBase.NyNonCheckControl import NyNonCheckControl
from Products.NaayaBase.NyValidation import NyValidation
from Products.NaayaBase.NyContainer import NyContainer
from Products.NaayaBase.NyAttributes import NyAttributes
from Products.NaayaBase.NyImageContainer import NyImageContainer
from Products.Localizer.LocalPropertyManager import LocalProperty
from Products.NaayaBase.NyProperties import NyProperties
from constants import *
from Products.NaayaBase.NyRoleManager import NyRoleManager
from Products.NaayaBase.NyAccess import NyAccess
from naaya.core.zope2util import DT2dt

#local imports
from Section import addSection
from Section import addSection_html
from invitations import InvitationsContainer, InvitationUsersTool
from comments_admin import CommentsAdmin

#module constants

METATYPE_OBJECT = METATYPE_TALKBACKCONSULTATION
LABEL_OBJECT = 'TalkBack Consultation'
PERMISSION_ADD_OBJECT = 'Naaya - Add Naaya TalkBack Consultation objects'
OBJECT_FORMS = []
OBJECT_CONSTRUCTORS = ['manage_addNyTalkBackConsultation_html',
                       'talkbackconsultation_add_html',
                       'addNyTalkBackConsultation']
OBJECT_ADD_FORM = 'talkbackconsultation_add_html'
DESCRIPTION_OBJECT = 'This is Naaya TalkBack Consultation type.'
PREFIX_OBJECT = 'tbcns'
ADDITIONAL_STYLE = open(ImageFile(
    'www/talkbackconsultation_style.css', globals()).path).read()
PROPERTIES_OBJECT = {
    'id':                  (0, '', ''),
    'title':               (1,
                            MUST_BE_NONEMPTY,
                            'The Title field must have a value.'),

    'description':         (0, '', ''),
    'start_date':          (0,
                            MUST_BE_DATETIME,
                            'The Start Date field must contain a valid date.'),

    'end_date':            (0,
                            MUST_BE_DATETIME,
                            'The End Date field must contain a valid date.'),

    'sortorder':           (0,
                            MUST_BE_POSITIV_INT,
                            'The Sort order field must contain a positive integer.'),

    'releasedate':         (0,
                            MUST_BE_DATETIME,
                            'The Release date field must contain a valid date.'),
    'allow_file':          (0, '', ''),
    'public_registration': (0, '', ''),
    'lang':                (0, '', '')
}

# this dictionary is updated at the end of the module
config = {
        'product': 'NaayaContent',
        'module': 'tbconsultation_item',
        'package_path': os.path.abspath(os.path.dirname(__file__)),
        'meta_type': 'Naaya TalkBack Consultation',
        'label': 'TalkBack Consultation',
        'permission': 'Naaya - Add Naaya TalkBack Consultation objects',
        'forms': [],
        'add_form': 'talkbackconsultation_add_html',
        'description': 'This is Naaya TalkBack Consultation type.',
        'properties': PROPERTIES_OBJECT,
        'default_schema': None,
        'schema_name': '',
        'import_string': '',
        '_module': sys.modules[__name__],
        'additional_style': ADDITIONAL_STYLE,
        'icon': os.path.join(os.path.dirname(__file__), 'www', 'NyTalkBackConsultation.gif'),
        '_misc': {
                'NyTalkBackConsultation.gif': ImageFile('www/NyTalkBackConsultation.gif', globals()),
                'NyTalkBackConsultation_marked.gif': ImageFile('www/NyTalkBackConsultation_marked.gif', globals()),
                'tb-editor.css': ImageFile('www/tb-editor.css', globals()),
            },
    }

talkbackconsultation_add_html = NaayaPageTemplateFile(
    'zpt/talkbackconsultation_add', globals(), 'tbconsultation_add')

def addNyTalkBackConsultation(self,
                              id='',
                              title='',
                              description='',
                              sortorder='',
                              start_date='',
                              end_date='',
                              public_registration='',
                              allow_file='',
                              allow_reviewer_invites=False,
                              contributor=None,
                              releasedate='',
                              lang=None,
                              REQUEST=None,
                              **kwargs):
    """
    Create a Naaya TalkBack Consultation type of object.
    """
    #process parameters
    id = self.utSlugify(id or title)
    try: sortorder = abs(int(sortorder))
    except: sortorder = DEFAULT_SORTORDER

    #check mandatory fiels
    l_referer = ''
    if REQUEST is not None: l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
    if not(l_referer == 'talkbackconsultation_manage_add' or \
           l_referer.find('talkbackconsultation_manage_add') != -1) and REQUEST:
        r = self.getSite().\
          check_pluggable_item_properties(
              METATYPE_TALKBACKCONSULTATION,
              id=id,
              title=title,
              sortorder=sortorder,
              start_date=start_date,
              end_date=end_date,
              public_registration=public_registration)
    else:
        r = []
    if not len(r):
        auth_user = self.REQUEST.AUTHENTICATED_USER.getUserName()
        #process parameters
        if contributor is None:
            contributor = auth_user
        if self.checkPermissionSkipApproval():
            approved, approved_by = 1, auth_user
        else:
            approved, approved_by = 0, None
        releasedate = self.process_releasedate(releasedate)
        if lang is None: lang = self.gl_get_selected_language()
        #check if the id is invalid (it is already in use)
        i = 0
        while self._getOb(id, None) is not None:
            i += 1
            id = '%s-%u' % (id, i)
        #create object
        ob = NyTalkBackConsultation(id, title, description, sortorder,
                                    start_date, end_date, public_registration,
                                    allow_file, allow_reviewer_invites,
                                    contributor, releasedate, lang)
        self.gl_add_languages(ob)
        ob.createDynamicProperties(
            self.processDynamicProperties(METATYPE_TALKBACKCONSULTATION, REQUEST, kwargs),
            lang)
        self._setObject(id, ob)
        #extra settings
        ob = self._getOb(id)
        ob.submitThis()
        ob.approveThis(approved, approved_by)
        ob.addDynProp()
        ob.updateRequestRoleStatus(public_registration, lang)
        self.recatalogNyObject(ob)
        self.notifyFolderMaintainer(self, ob)
        #log post date
        auth_tool = self.getAuthenticationTool()
        auth_tool.changeLastPost(contributor)
        #redirect if case
        if REQUEST is not None:
            if l_referer == 'talkbackconsultation_manage_add' or \
               l_referer.find('talkbackconsultation_manage_add') != -1:
                return self.manage_main(self, REQUEST, update_menu=1)
            elif l_referer == 'talkbackconsultation_add_html':
                self.setSession('referer', self.absolute_url())
                REQUEST.RESPONSE.redirect(
                    '%s/messages_html' % self.absolute_url()
                )
        else:
            return id
    else:
        if REQUEST is not None:
            self.setSessionErrors(r)
            self.set_pluggable_item_session(
                METATYPE_TALKBACKCONSULTATION,
                id=id,
                title=title,
                description=description,
                sortorder=sortorder,
                releasedate=releasedate,
                start_date=start_date,
                end_date=end_date,
                allow_file=allow_file,
                allow_reviewer_invites=allow_reviewer_invites,
                public_registration=public_registration,
                lang=lang
            )
            REQUEST.RESPONSE.redirect(
                '%s/talkbackconsultation_add_html' % self.absolute_url()
            )
        else:
            raise Exception, '%s' % ', '.join(r)

class NyTalkBackConsultation(NyRoleManager,
                             NyAttributes,
                             Implicit,
                             NyProperties,
                             NyContainer,
                             NyNonCheckControl,
                             utils):
    """ """

    meta_type = METATYPE_TALKBACKCONSULTATION
    meta_label = LABEL_OBJECT

    meta_types = [
        {'name': METATYPE_TALKBACKCONSULTATION_SECTION, 'action': 'addSection',
            'permission': PERMISSION_MANAGE_TALKBACKCONSULTATION},
    ]


    icon = 'misc_/NaayaContent/NyTalkBackConsultation.gif'
    icon_marked = 'misc_/NaayaContent/NyTalkBackConsultation_marked.gif'

    title = LocalProperty('title')
    description = LocalProperty('description')

    security = ClassSecurityInfo()

    edit_access = NyAccess('edit_access', {
        PERMISSION_REVIEW_TALKBACKCONSULTATION: "Submit comments",
        PERMISSION_MANAGE_TALKBACKCONSULTATION: "Administer consultation",
        PERMISSION_INVITE_TO_TALKBACKCONSULTATION: "Send invitations",
    })

    section_sort_order = tuple()

    def __init__(self,
                 id,
                 title,
                 description,
                 sortorder,
                 start_date,
                 end_date,
                 public_registration,
                 allow_file,
                 allow_reviewer_invites,
                 contributor,
                 releasedate,
                 lang):
        """ """


        self.id = id
        self.contributor = contributor
        NyContainer.__dict__['__init__'](self)
        self.save_properties(title,
                             description,
                             sortorder,
                             start_date,
                             end_date,
                             public_registration,
                             allow_file,
                             allow_reviewer_invites,
                             releasedate,
                             lang)

        NyProperties.__dict__['__init__'](self)
        self.invitations = InvitationsContainer('invitations')
        self.submitted = 1

    def set_allow_reviewer_invites(self, allow):
        perm = '_Naaya___Invite_to_TalkBack_Consultation_Permission'
        roles = getattr(self, perm, [])

        if allow and 'Reviewer' not in roles:
            roles.append('Reviewer')
        elif not allow and 'Reviewer' in roles:
            roles.remove('Reviewer')

        if roles:
            setattr(self, perm, roles)
        else:
            if hasattr(self, perm):
                delattr(self, perm)

    def get_allow_reviewer_invites(self):
        perm = '_Naaya___Invite_to_TalkBack_Consultation_Permission'
        roles = getattr(self, perm, [])
        return ('Reviewer' in roles)

    allow_reviewer_invites = property(get_allow_reviewer_invites,
                                      set_allow_reviewer_invites)

    security.declarePrivate('save_properties')
    def save_properties(self,
                        title,
                        description,
                        sortorder,
                        start_date,
                        end_date,
                        public_registration,
                        allow_file,
                        allow_reviewer_invites,
                        releasedate,
                        lang):

        self._setLocalPropValue('title', lang, title)
        self._setLocalPropValue('description', lang, description)

        if not hasattr(self, 'imageContainer'):
            self.imageContainer = NyImageContainer(self, True)

        if start_date:
            self.start_date = self.utConvertStringToDateTimeObj(start_date)
        else:
            self.start_date = self.utGetTodayDate()

        if end_date:
            self.end_date = self.utConvertStringToDateTimeObj(end_date)
        else:
            self.end_date = self.utGetTodayDate()

        try: self.sortorder = abs(int(sortorder))
        except: self.sortorder = DEFAULT_SORTORDER

        self.releasedate = releasedate
        self.public_registration = public_registration
        self.allow_file = allow_file
        self.allow_reviewer_invites = allow_reviewer_invites

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION,
                              'saveProperties')
    def saveProperties(self,
                       title='',
                       description='',
                       sortorder='',
                       start_date='',
                       end_date='',
                       public_registration='',
                       allow_file='',
                       allow_reviewer_invites=False,
                       lang='',
                       REQUEST=None):
        """ """


        if not title:
            self.setSession('title', title)
            self.setSession('description', description)
            self.setSessionErrorsTrans('The Title field must have a value.')
            if REQUEST:
                return REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' %
                                                 (self.absolute_url(), lang))
            else:
                raise ValueError('The title field must have a value.')

        releasedate = self.releasedate
        self.updateRequestRoleStatus(public_registration, lang)
        self.save_properties(title, description, sortorder, start_date, end_date,
                             public_registration, allow_file, allow_reviewer_invites,
                             releasedate, lang)

        if REQUEST:
            self.setSessionInfoTrans(MESSAGE_SAVEDCHANGES,
                                     date=self.utGetTodayDate())
            REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), lang))

    security.declarePrivate('addDynProp')
    def addDynProp(self):
        """ """
        dynprop_tool = self.getDynamicPropertiesTool()
        if not hasattr(dynprop_tool, METATYPE_OBJECT):
            dynprop_tool.manage_addDynamicPropertiesItem(id=METATYPE_OBJECT, title=METATYPE_OBJECT)
            dynprop_tool._getOb(METATYPE_OBJECT).manageAddDynamicProperty(id='show_contributor_request_role', name='Allow visitors to register as reviewers for this consultation', type='boolean')

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION, 'updateRequestRoleStatus')
    def updateRequestRoleStatus(self, public_registration, lang):
        """ Allow public registration for this consultation """
        if public_registration: self.updateDynamicProperties(self.processDynamicProperties(METATYPE_TALKBACKCONSULTATION, {'show_contributor_request_role': 'on'}), lang)
        if not public_registration: self.updateDynamicProperties(self.processDynamicProperties(METATYPE_TALKBACKCONSULTATION, {'show_contributor_request_role': ''}), lang)

    security.declareProtected(view, 'get_consultation')
    def get_consultation(self):
        return self

    security.declareProtected(view, 'list_sections')
    def list_sections(self):
        """ """
        metatypes = [METATYPE_TALKBACKCONSULTATION_SECTION]
        sections = dict(self.objectItems(metatypes))

        output = []
        for section_id in self.section_sort_order:
            if section_id in sections:
                output.append(sections.pop(section_id))

        output.extend(sorted(sections.values(),
                             key=operator.attrgetter('title')))

        return output

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION,
                              'save_sort_order')
    def save_sort_order(self, sort_section_id, REQUEST=None):
        """ save the sort order of sections """
        self.section_sort_order = tuple(sort_section_id)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    _comments_atom = NaayaPageTemplateFile('zpt/comments_atom', globals(),
                                           'tbconsultation_comments_atom')
    security.declareProtected(view, 'comments_atom')
    def comments_atom(self, REQUEST=None, days=2):
        """ ATOM feed with consultation comments """

        if isinstance(days, basestring):
            try:
                days = int(days)
            except:
                days = 2

        cutoff = DateTime() - days
        comments_list = []
        for section in self.list_sections():
            for paragraph in section.get_paragraphs():
                for comment in paragraph.get_comments():
                    if comment.comment_date < cutoff:
                        continue
                    if not comment.approved:
                        continue
                    comments_list.append(comment)
        comments_list.sort(key=operator.attrgetter('comment_date'),
                           reverse=True)

        if comments_list:
            feed_updated = comments_list[0].comment_date
        else:
            feed_updated = DateTime()

        def atom_date_format(date):
            d = DT2dt(date).strftime('%Y-%m-%dT%H:%M:%S%z')
            return d[:-2] + ':' + d[-2:]

        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'application/atom+xml')

        return self._comments_atom(comments_list=comments_list,
                                   atom_date_format=atom_date_format,
                                   feed_updated=feed_updated)

    security.declareProtected(view, 'get_start_date')
    def get_start_date(self):
        """ Returns the start date in dd/mm/yyyy string format. """

        return self.utConvertDateTimeObjToString(self.start_date)

    security.declareProtected(view, 'get_end_date')
    def get_end_date(self):
        """ Returns the end date in dd/mm/yyyy string format. """

        return self.utConvertDateTimeObjToString(self.end_date)

    security.declareProtected(view, 'get_days_left')
    def get_days_left(self):
        """ Returns the remaining days for the consultation or the number of days before it starts """

        today = self.utGetTodayDate().earliestTime()
        if not self.start_date or not self.end_date:
            return (1, 0)

        after_end_date = self.end_date + 1
        if self.start_date.lessThanEqualTo(today):
            return (1, int(str(after_end_date - today).split('.')[0]))
        else:
            return (0, int(str(self.start_date - today).split('.')[0]))

    security.declareProtected(view_management_screens, 'manage_options')
    def manage_options(self):
        """ """

        l_options = (NyContainer.manage_options[0],)
        l_options += ({'label': 'View', 'action': 'index_html'},) + \
                  NyContainer.manage_options[3:8]
        return l_options

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION,
                              'delete_sections')
    def delete_sections(self, del_section_id, REQUEST=None):
        """ remove the specified sections """
        self.manage_delObjects(list(del_section_id))
        self.setSessionInfoTrans('Removed ${count} sections.',
                                 count=str(len(del_section_id)))
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url())

    def get_user_name(self):
        # first, check if we have an invite key
        invitation = self.invitations.get_current_invitation(self.REQUEST)
        if invitation is not None:
            return invitation.name

        # no invite key; look for current Zope user
        auth_tool = self.getAuthenticationTool()
        userid = auth_tool.get_current_userid()

        if userid is None: # anonymous user
            return None

        name = auth_tool.name_from_userid(userid)
        if name == '':
            name = userid
        return name

    def get_user_name_or_userid(self, userid=None):
        if userid is None:
            return self.get_user_name()

        auth_tool = self.getAuthenticationTool()
        name = auth_tool.name_from_userid(userid)
        if name == '':
            name = userid

        return name

    def checkTalkBackConsultationUser(self):
        """
        Checks if the user is logged in and has reviewer rights:
        0 if user is anonymous,
        1 if user has reviewer role
        2 if user doesn't have reviewer role
        """
        review_check = self.checkPermissionReviewTalkBackConsultation()

        if self.isAnonymousUser(): return 0
        elif review_check: return 1
        elif not review_check: return 2

    security.declareProtected(view, 'check_cannot_comment')
    def check_cannot_comment(self):
        """ """

        if not self.checkPermissionReviewTalkBackConsultation():
            if self.isAnonymousUser():
                return 'not-logged-in'
            else:
                return 'no-permission'

        if self.get_days_left()[1] <= 0:
            return 'deadline-reached'

    security.declareProtected(
        PERMISSION_COMMENTS_ADD, 'log_in_authenticated')
    def log_in_authenticated(self, REQUEST=None):
        """ Log in user and redirect to TalkBack Consultation index """
        if REQUEST is not None:
            self.REQUEST.RESPONSE.redirect(self.absolute_url())

    #permissions
    def checkPermissionReviewTalkBackConsultation(self):
        """
        Check for reviewing the TalkBack Consultation.
        """
        return self.checkPermission(PERMISSION_REVIEW_TALKBACKCONSULTATION)

    def checkPermissionManageTalkBackConsultation(self):
        """
        Check for managing the TalkBack Consultation.
        """
        return self.checkPermission(PERMISSION_MANAGE_TALKBACKCONSULTATION)

    def checkPermissionInviteToTalkBackConsultation(self):
        """
        Check for inviting others to the TalkBack Consultation.
        """
        return self.checkPermission(PERMISSION_INVITE_TO_TALKBACKCONSULTATION)

    security.declareProtected(view, 'custom_editor')
    def custom_editor(self, editor_tool, lang, dom_id):
        extra_options = {
            'content_css': self.absolute_url() +
                            '/misc_/NaayaContent/tb-editor.css',
            'theme_advanced_buttons1':
                'bold,italic,underline,strikethrough,sub,sup,forecolor,'
                    'backcolor,removeformat,separator,'
                'bullist,numlist,separator,'
                'justifyleft,justifycenter,justifyright,justifyfull,separator,'
                'link,unlink,hr,image,separator,'
                'pastetext,pasteword,cleanup,code,help',
            'theme_advanced_buttons2': '',
        }
        return editor_tool.render(dom_id, lang, image_support=True,
                                  extra_options=extra_options)

    addSection = addSection

    #zmi pages
    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/talkbackconsultation_manage_edit', globals())

    #site pages
    security.declareProtected(view, 'index_html')
    index_html = NaayaPageTemplateFile('zpt/talkbackconsultation_index', globals(),
                                       'tbconsultation_index')

    # standard_template_macro, header and footer templates are proxied
    # since invited reviewers have "View" permission only in this folder;
    # if the consultation is restricted, they would not be able to see
    # consultation pages.
    def standard_html_header(self, *args, **kwargs):
        return self.aq_parent.standard_html_header(*args, **kwargs)

    def standard_html_footer(self, *args, **kwargs):
        return self.aq_parent.standard_html_footer(*args, **kwargs)

    def standard_template_macro(self, *args, **kwargs):
        return self.aq_parent.standard_template_macro(*args, **kwargs)

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION, 'edit_html')
    edit_html = NaayaPageTemplateFile('zpt/talkbackconsultation_edit', globals(),
                                      'tbconsultation_edit')

    security.declareProtected(PERMISSION_MANAGE_TALKBACKCONSULTATION, 'section_add_html')
    section_add_html = addSection_html

    __allow_groups__ = InvitationUsersTool()
    _View_Permission = ['InvitedReviewer']
    _Naaya___Review_TalkBack_Consultation_Permission = ['InvitedReviewer']
    __ac_roles__ = ['InvitedReviewer']

    admin_comments = CommentsAdmin('admin_comments')

InitializeClass(NyTalkBackConsultation)
manage_addNyTalkBackConsultation_html = PageTemplateFile(
    'zpt/talkbackconsultation_manage_add', globals())
manage_addNyTalkBackConsultation_html.kind = METATYPE_TALKBACKCONSULTATION
manage_addNyTalkBackConsultation_html.action = 'addNyTalkBackConsultation'
config.update({
    'constructors': (manage_addNyTalkBackConsultation_html, addNyTalkBackConsultation),
    'folder_constructors': [
            # NyFolder.manage_addNyTalkBackConsultation_html = manage_addNyTalkBackConsultation_html
            ('manage_addNyTalkBackConsultation_html', manage_addNyTalkBackConsultation_html),
            ('talkbackconsultation_add_html', talkbackconsultation_add_html),
            ('addNyTalkBackConsultation', addNyTalkBackConsultation),
        ],
    'add_method': addNyTalkBackConsultation,
    'validation': issubclass(NyTalkBackConsultation, NyValidation),
    '_class': NyTalkBackConsultation,
})

def get_config():
    return config

def register_permissions():
    from Products.Naaya.NySite import register_naaya_permission
    register_naaya_permission(PERMISSION_REVIEW_TALKBACKCONSULTATION,
                              'TalkBack Consultation - submit review')
    register_naaya_permission(PERMISSION_INVITE_TO_TALKBACKCONSULTATION,
                              'TalkBack Consultation - invite participants')
    register_naaya_permission(PERMISSION_MANAGE_TALKBACKCONSULTATION,
                              'TalkBack Consultation - manage')
