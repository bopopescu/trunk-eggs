# Python imports
import os.path
import re

# Zope imports
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
import zLOG

# Naaya imports
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile
from Products.NaayaCore.EmailTool.EmailPageTemplate import EmailPageTemplate
from Products.NaayaCore.EmailTool.EmailTool import (save_bulk_email,
                                                    get_bulk_emails,
                                                    get_bulk_email,
                                                    _mail_in_queue,
                                                    check_cached_valid_emails,
                                                    export_email_list_xcel)
import simplejson as json
from Products.NaayaCore.managers.utils import import_non_local

# naaya.content.meeting imports
from Products.NaayaCore.AuthenticationTool.utils import getUserEmail, findUsers
from naaya.core.utils import is_valid_email
from naaya.content.meeting import WAITING_ROLE
from naaya.core.zope2util import path_in_site
from permissions import PERMISSION_ADMIN_MEETING


def configureEmailNotifications(site):
    """ Add the email templates to EmailTool """
    templates = [
        {'id': 'naaya.content.meeting.email_signup',
         'title': 'Signup notification',
         'file': 'zpt/email_signup.zpt'},
        {'id': 'naaya.content.meeting.email_account_subscription',
         'title': 'Account subscription',
         'file': 'zpt/email_account_subscription.zpt'},
        {'id': 'naaya.content.meeting.email_signup_accepted',
         'title': 'Signup accepted',
         'file': 'zpt/email_signup_accepted.zpt'},
        {'id': 'naaya.content.meeting.email_signup_rejected',
         'title': 'Signup rejected',
         'file': 'zpt/email_signup_rejected.zpt'},
        {'id': 'naaya.content.meeting.email_account_subscription_accepted',
         'title': 'Account subscription accepted',
         'file': 'zpt/email_account_subscription_accepted.zpt'},
        {'id': 'naaya.content.meeting.email_account_subscription_rejected',
         'title': 'Account subscription rejected',
         'file': 'zpt/email_account_subscription_rejected.zpt'},
        ]
    email_tool = site.getEmailTool()
    for t in templates:
        f = open(os.path.join(os.path.dirname(__file__), t['file']), 'r')
        content = f.read()
        f.close()

        t_ob = email_tool._getOb(t['id'], None)
        if t_ob is None:
            email_tool.manage_addEmailTemplate(t['id'], t['title'], content)


class EmailSender(SimpleItem):
    security = ClassSecurityInfo()

    title = 'Send Emails'

    def __init__(self, id):
        """ """
        self.id = id

    def getMeeting(self):
        return self.aq_parent

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'index_html')

    def index_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent(
            {'here': self,
             'meeting': self.getMeeting()},
            'naaya.content.meeting.email_index')

    def _send_email(self, p_from, p_to, p_cc, p_subject, p_content,
                    only_to=False, only_cc=False):
        """ """
        try:
            email_tool = self.getEmailTool()
            return email_tool.sendEmail(p_content=p_content,
                                        p_to=p_to,
                                        p_cc=p_cc,
                                        p_from=p_from,
                                        p_subject=p_subject,
                                        only_to=only_to,
                                        only_cc=only_cc)
        except Exception, e:
            zLOG.LOG('naaya.content.meeting.email', zLOG.WARNING,
                     'Email sending failed for template - %s' % str(e))
            return 0

    def _send_email_with_template(self, template_id, p_from, p_to, mail_opts):
        """ """
        try:
            email_tool = self.getEmailTool()

            template_text = email_tool._getOb(template_id).body
            template = EmailPageTemplate(template_id, template_text)
            mail_data = template.render_email(**mail_opts)

            p_subject = mail_data['subject']
            p_content = mail_data['body_text']

            return email_tool.sendEmail(p_content=p_content,
                                        p_to=p_to,
                                        p_from=p_from,
                                        p_subject=p_subject)
        except Exception, e:
            zLOG.LOG('naaya.content.meeting.email', zLOG.WARNING,
                     'Email sending failed for template %s - %s' %
                     (template_id, str(e)))
            return 0

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'send_email')

    def send_email(self, from_email, subject, body_text, cc_emails, REQUEST,
                   to_uids=None):
        """ """
        errors = []
        if not to_uids:
            to_uids = []
        if not (to_uids or cc_emails):
            errors.append('Please select at least on recipient')
        if not (subject or body_text):
            errors.append('Subject and message body cannot both be empty')
        for email in cc_emails:
            if not is_valid_email(email):
                errors.append('Invalid email "%s" in CC field' % email)
        if errors:
            self.setSessionErrorsTrans(errors)
            return REQUEST.RESPONSE.redirect(REQUEST.HTTP_REFERER)
        participants = self.getParticipants()
        subscriptions = participants.getSubscriptions()
        signup_emails = [participants.getAttendeeInfo(uid)['email']
                         for uid in to_uids if
                         subscriptions._is_signup(uid)]
        account_emails = [participants.getAttendeeInfo(uid)['email']
                          for uid in to_uids if not
                          subscriptions._is_signup(uid)]
        to_emails = signup_emails + account_emails

        if (self.is_eionet_meeting and
                'eionet-nfp@roles.eea.eionet.europa.eu' not in cc_emails):
            cc_emails.append('eionet-nfp@roles.eea.eionet.europa.eu')
            # TODO validate cc_emails

        # We need to send the emails to signups one by one since each email
        # might be different (if they contain links to documents for
        # which the authentication keys is inserted into the link)
        for uid in to_uids:
            if subscriptions._is_signup(uid):
                signup_email = participants.getAttendeeInfo(uid)['email']
                signup_body_text = self.insert_auth_link(body_text, uid)
                result = self._send_email(
                    from_email, [signup_email], cc_emails, subject,
                    signup_body_text, only_to=True)

        if account_emails:
            result = self._send_email(from_email, account_emails, cc_emails,
                                      subject, body_text)

        save_bulk_email(self.getSite(), to_emails, from_email, subject,
                        body_text,
                        where_to_save=path_in_site(self.getMeeting()),
                        addr_cc=cc_emails)

        return self.getFormsTool().getContent(
            {'here': self,
             'meeting': self.getMeeting(),
             'result': result},
            'naaya.content.meeting.email_sendstatus')

    def insert_auth_link(self, body_text, key):
        meeting_url = self.getMeeting().absolute_url()
        urls = re.findall(
            'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
            '(?:%[0-9a-fA-F][0-9a-fA-F]))+', body_text)
        for url in urls:
            if meeting_url in url:
                body_text = body_text.replace(
                    url,
                    '%s/participants/subscriptions/welcome?key=%s&came_from=%s'
                    % (meeting_url, key, url))
        return body_text

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'send_signup_email')

    def send_signup_email(self, signup):
        """ """
        meeting = self.getMeeting()
        site = self.getSite()
        from_email = site.administrator_email
        to_email = [meeting.contact_email]
        user_email = getUserEmail(site,
                                  self.REQUEST.AUTHENTICATED_USER.getId())
        if user_email and user_email not in to_email:
            to_email.append(user_email)

        mail_opts = {'meeting': meeting,
                     'contact_person': meeting.contact_person,
                     'name': signup.name,
                     '_translate': self.getPortalI18n().get_translation}

        return self._send_email_with_template(
            'naaya.content.meeting.email_signup', from_email, to_email,
            mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING,
                              'send_account_subscription_email')

    def send_account_subscription_email(self, account_subscription):
        """ """
        meeting = self.getMeeting()
        site = self.getSite()
        from_email = site.administrator_email
        to_email = meeting.contact_email

        mail_opts = {'meeting': meeting,
                     'contact_person': meeting.contact_person,
                     'name': account_subscription.name,
                     '_translate': self.getPortalI18n().get_translation}

        return self._send_email_with_template(
            'naaya.content.meeting.email_account_subscription',
            from_email, to_email, mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING,
                              'send_signup_accepted_email')

    def send_signup_accepted_email(self, signup, resend=False):
        """ """
        meeting = self.getMeeting()
        subscriptions = meeting.getParticipants().getSubscriptions()
        account_info = meeting.getParticipants()._get_attendees()[signup.key]
        from_email = meeting.contact_email
        to_email = signup.email
        login_url = subscriptions.absolute_url() + '/welcome?key=' + signup.key

        mail_opts = {'meeting': meeting,
                     'name': signup.name,
                     'login_url': login_url,
                     'on_waiting_list': account_info['role'] == WAITING_ROLE,
                     '_translate': self.getPortalI18n().get_translation,
                     'resend': resend
                     }

        return self._send_email_with_template(
            'naaya.content.meeting.email_signup_accepted', from_email,
            to_email, mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING,
                              'send_signup_rejected_email')

    def send_signup_rejected_email(self, signup):
        """ """
        meeting = self.getMeeting()
        from_email = meeting.contact_email
        to_email = signup.email

        mail_opts = {'meeting': meeting,
                     'name': signup.name,
                     '_translate': self.getPortalI18n().get_translation}

        return self._send_email_with_template(
            'naaya.content.meeting.email_signup_rejected', from_email,
            to_email, mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING,
                              'send_account_subscription_accepted_email')

    def send_account_subscription_accepted_email(self, account_subscription,
                                                 resend=False):
        """ """
        meeting = self.getMeeting()
        uid = account_subscription.uid
        account_info = meeting.getParticipants().getAttendeeInfo(uid)
        from_email = meeting.contact_email
        to_email = account_subscription.email

        mail_opts = {'meeting': meeting,
                     'uid': uid,
                     'name': account_subscription.name,
                     'on_waiting_list': account_info['role'] == WAITING_ROLE,
                     '_translate': self.getPortalI18n().get_translation,
                     'resend': resend
                     }
        return self._send_email_with_template(
            'naaya.content.meeting.email_account_subscription_accepted',
            from_email, to_email, mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING,
                              'send_account_subscription_rejected_email')

    def send_account_subscription_rejected_email(self, account_subscription):
        """ """
        meeting = self.getMeeting()
        from_email = meeting.contact_email
        to_email = account_subscription.email

        mail_opts = {'meeting': meeting,
                     'name': account_subscription.name,
                     '_translate': self.getPortalI18n().get_translation}
        return self._send_email_with_template(
            'naaya.content.meeting.email_account_subscription_rejected',
            from_email, to_email, mail_opts)

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'saved_emails')

    def saved_emails(self, REQUEST=None, RESPONSE=None):
        """ Display all saved bulk emails """
        emails = get_bulk_emails(self.getSite(),
                                 where_to_read=path_in_site(self.getMeeting()))
        import_non_local('email', 'std_email')
        from std_email import email as standard_email
        for email in emails:
            subject, encoding = standard_email.Header.decode_header(
                email['subject'])[0]
            if encoding:
                email['subject'] = subject.decode(encoding)
            else:
                email['subject'] = subject
            recipients = []
            if email['recipients'] is None:
                email['recipients'] = []
            for recp in email['recipients']:
                recipients.extend(re.split(',|;', recp.replace(' ', '')))
            email['recipients'] = recipients
            cc_recipients = []
            if email['cc_recipients'] is None:
                email['cc_recipients'] = []
            for recp in email['cc_recipients']:
                cc_recipients.extend(re.split(',|;', recp.replace(' ', '')))
            email['cc_recipients'] = cc_recipients
        return self.getFormsTool().getContent(
            {'here': self,
             'emails': emails,
             'meeting': self.getMeeting()},
            'naaya.content.meeting.email_archive')

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'saved_emails_export')

    def saved_emails_export(self, REQUEST=None, RESPONSE=None):
        """ Aggregate an xcel file from emails on disk
        (just like saved_emails does to populate the web page)"""
        if not REQUEST:
            RESPONSE.badRequestError("MALFORMED_URL")
        headers = REQUEST.form.get('headers')
        keys = REQUEST.form.get('keys')
        ids = REQUEST.form.get('id')
        if not headers or not keys:
            RESPONSE.badRequestError("MALFORMED_URL")
        headers = headers.split(',')
        keys = keys.split(',')
        if len(headers) != len(keys):
            RESPONSE.badRequestError("MALFORMED_URL")

        RESPONSE.setHeader('Content-Type', 'application/vnd.ms-excel')
        RESPONSE.setHeader('Content-Disposition',
                           'attachment; filename=meeting_email_list.xls')
        cols = zip(headers, keys)
        return export_email_list_xcel(
            self.getSite(), cols, ids,
            where_to_read=path_in_site(self.getMeeting()))

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'view_email')

    def view_email(self, filename, REQUEST=None, RESPONSE=None):
        """ Display a specfic saved email """
        email = get_bulk_email(self.getSite(), filename,
                               where_to_read=path_in_site(self.getMeeting()))
        return self.getFormsTool().getContent(
            {'here': self,
             'email': email,
             'meeting': self.getMeeting()},
            'naaya.content.meeting.email_view_email')

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'check_emails')

    def check_emails(self, REQUEST=None, RESPONSE=None):
        """Return already resolved email addresses
        and a list with those to be resolved by a different call"""
        emails = REQUEST.get("emails[]")
        if not emails:
            return None
        invalid, not_resolved = check_cached_valid_emails(self, emails)
        return json.dumps({'invalid': invalid, 'notResolved': not_resolved})

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'mail_in_queue')

    def mail_in_queue(self, filename):
        """ Check if a specific message is still in queue """
        # removed recipients from COMMON_KEYS because of signup
        # recipients splitting
        COMMON_KEYS = ['sender', 'subject', 'content', 'date']
        check_values = {}
        archived_email = get_bulk_email(
            self.getSite(), filename,
            where_to_read=path_in_site(self.getMeeting()))
        for key in COMMON_KEYS:
            check_values[key] = archived_email[key]
        return _mail_in_queue(self.getSite(), filename, check_values)

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'searchUsers')

    def findUsers(self, search_param, search_term):
        """ """
        if len(search_term) == 0:
            return []
        return json.dumps(findUsers(self.getSite(), search_param, search_term))

NaayaPageTemplateFile('zpt/email_index', globals(),
                      'naaya.content.meeting.email_index')
NaayaPageTemplateFile('zpt/email_sendstatus', globals(),
                      'naaya.content.meeting.email_sendstatus')
NaayaPageTemplateFile('zpt/email_archive', globals(),
                      'naaya.content.meeting.email_archive')
NaayaPageTemplateFile('zpt/email_view_email', globals(),
                      'naaya.content.meeting.email_view_email')
