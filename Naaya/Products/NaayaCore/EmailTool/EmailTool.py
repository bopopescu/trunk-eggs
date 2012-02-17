"""
This tool provides e-mail management in a Naaya Site. Configurable e-mail
templates, e-mail sending and logging of all e-mail traffic.

"""

import os
import time
import smtplib
import cStringIO
from urlparse import urlparse
import logging
import email.Utils, email.Charset, email.Header
from email.MIMEText import MIMEText

from zope.component import queryUtility, getGlobalSiteManager
from zope.sendmail.interfaces import IMailDelivery
from zope.sendmail.mailer import SMTPMailer
from zope.deprecation import deprecate
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.NaayaCore.constants import *
import EmailTemplate
from EmailSender import build_email
from naaya.core.permissions import naaya_admin
from naaya.core.utils import force_to_unicode


mail_logger = logging.getLogger('naaya.core.email')

try:
    import email.message
except ImportError:
    def create_plain_message(body_bytes):
        """
        This is just a simple factory for message instance (with payload)
        that works with both email.MIMEText (python 2.4)
        and email.message (python 2.6)

        """
        return MIMEText(body_bytes, 'plain')
else:
    def create_plain_message(body_bytes):
        message = email.message.Message()
        message.set_payload(body_bytes)
        return message

def manage_addEmailTool(self, REQUEST=None):
    """ """
    ob = EmailTool(ID_EMAILTOOL, TITLE_EMAILTOOL)
    self._setObject(ID_EMAILTOOL, ob)
    self._getOb(ID_EMAILTOOL).loadDefaultData()
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class EmailTool(Folder):
    """ """

    meta_type = METATYPE_EMAILTOOL
    icon = 'misc_/NaayaCore/EmailTool.gif'

    manage_options = (
        Folder.manage_options[:1]
        +
        (
            {'label': 'Settings', 'action': 'manage_settings_html'},
        )
        +
        Folder.manage_options[3:]
    )

    meta_types = (
        {'name': METATYPE_EMAILTEMPLATE, 'action': 'manage_addEmailTemplateForm', 'permission': PERMISSION_ADD_NAAYACORE_TOOL},
    )
    all_meta_types = meta_types

    manage_addEmailTemplateForm = EmailTemplate.manage_addEmailTemplateForm
    manage_addEmailTemplate = EmailTemplate.manage_addEmailTemplate

    security = ClassSecurityInfo()

    def __init__(self, id, title):
        """ """
        self.id = id
        self.title = title

    security.declarePrivate('loadDefaultData')
    def loadDefaultData(self):
        #load default stuff
        pass

    def _guess_from_address(self):
        if self.portal_url != '':
            return 'notifications@%s' % urlparse(self.getSite().get_portal_domain())[1]
        else:
            return 'notifications@%s' % urlparse(self.REQUEST.SERVER_URL)[1]

    @deprecate('_get_from_address renamed to get_addr_from')
    def _get_from_address(self):
        return self.get_addr_from()

    security.declarePrivate('get_addr_from')
    def get_addr_from(self):
        """
        Get "From:" address, to use in mails originating from this portal. If
        no such address is configured then we attempt to guess it.
        """
        addr_from = self.getSite().mail_address_from
        return addr_from or self._guess_from_address()

    _errors_report = PageTemplateFile('zpt/configuration_errors_report', globals())
    security.declareProtected(naaya_admin, 'configuration_errors_report')
    def configuration_errors_report(self):
        errors = []
        if not (self.mail_server_name and self.mail_server_port):
            errors.append('Mail server address/port not configured')
        if not self.get_addr_from():
            errors.append('"From" address not configured')
        return self._errors_report(errors=errors)

    #api
    security.declarePrivate('sendEmail')
    def sendEmail(self, p_content, p_to, p_from, p_subject, _immediately=False):
        """
        Send email message on transaction commit. If the transaction fails,
        the message is discarded.
        """
        if not isinstance(p_to, list):
            p_to = [e.strip() for e in p_to.split(',')]

        p_to = filter(None, p_to) # filter out blank recipients

        try:
            site = self.getSite()
            site_path = '/'.join(site.getPhysicalPath())
        except:
            site = None
            site_path = '[no site]'

        try:
            if diverted_mail is not None: # we're inside a unit test
                diverted_mail.append([p_content, p_to, p_from, p_subject])
                return 1

            delivery = delivery_for_site(self.getSite())
            if delivery is None:
                mail_logger.info('Not sending email from %r because mail '
                                 'server is not configured',
                                 site_path)
                return 0

            if not p_from:
                mail_logger.info('Not sending email from %r - no sender',
                                 site_path)
                return 0

            if not p_to:
                mail_logger.info('Not sending email from %r - no recipients',
                                 site_path)
                return 0

            if _immediately:
                delivery = _ImmediateDelivery(delivery)

            mail_logger.info('Sending email from site: %r '
                             'to: %r subject: %r',
                             site_path, p_to, p_subject)
            l_message = create_message(p_content, p_to, p_from, p_subject)
            send_by_delivery(delivery, p_from, p_to, l_message)
            return 1

        except:
            mail_logger.error('Did not send email from site: %r to: %r '
                              'because an error occurred',
                              site_path, p_to)
            if site is not None:
                self.getSite().log_current_error()
            return 0

    security.declarePrivate('sendEmailImmediately')
    def sendEmailImmediately(self, *args, **kwargs):
        """
        Send email message straight away, without waiting for transaction
        commit. Useful when sending error emails because the transaction
        will probably be aborted.
        """
        kwargs['_immediately'] = True
        self.sendEmail(*args, **kwargs)

    #zmi actions
    security.declareProtected(view_management_screens, 'manageSettings')
    def manageSettings(self, mail_server_name='', mail_server_port='', administrator_email='', mail_address_from='', notify_on_errors_email='', REQUEST=None):
        """ """
        site = self.getSite()
        try: mail_server_port = int(mail_server_port)
        except: mail_server_port = site.mail_server_port
        site.mail_server_name = mail_server_name
        site.mail_server_port = mail_server_port
        site.mail_address_from = mail_address_from
        site.administrator_email = administrator_email
        site.notify_on_errors_email = notify_on_errors_email
        self._p_changed = 1
        if REQUEST:
            REQUEST.RESPONSE.redirect('manage_settings_html?save=ok')

    #zmi pages
    security.declareProtected(view_management_screens, 'manage_settings_html')
    manage_settings_html = PageTemplateFile('zpt/email_settings', globals())

InitializeClass(EmailTool)

diverted_mail = None
def divert_mail(enabled=True):
    global diverted_mail
    if enabled:
        diverted_mail = []
        return diverted_mail
    else:
        diverted_mail = None

def safe_header(value):
    """ prevent header injection attacks (the email library doesn't) """
    if '\n' in value:
        return email.Header.Header(value.encode('utf-8'), 'utf-8')
    else:
        return value

def hack_to_use_quopri(message):
    """
    force message payload to be encoded using quoted-printable
    http://mail.python.org/pipermail/baypiggies/2008-September/003984.html
    """

    charset = email.Charset.Charset('utf-8')
    charset.header_encoding = email.Charset.QP
    charset.body_encoding = email.Charset.QP

    del message['Content-Transfer-Encoding']
    message.set_charset(charset)

def send_by_delivery(delivery, p_from, p_to, message):
    """
    Send `message` email, where `message` is a MIMEText/Message instance created
    by create_message.
    Knows how to handle repoze.sendmail 2.3 differences in `message` arg type.

    """
    try:
        delivery.send(p_from, p_to, message.as_string())
    except AssertionError, e:
        if (e.args and
            e.args[0] == 'Message must be instance of email.message.Message'):
            delivery.send(p_from, p_to, message)
        else:
            raise

def create_message(text, addr_to, addr_from, subject):
    if isinstance(addr_to, basestring):
        addr_to = (addr_to,)
    addr_to = ', '.join(addr_to)
    subject = force_to_unicode(subject)
    text = force_to_unicode(text)

    message = create_plain_message(text.encode('utf-8'))
    hack_to_use_quopri(message)
    message['To'] = safe_header(addr_to)
    message['From'] = safe_header(addr_from)
    message['Subject'] = safe_header(subject)
    message['Date'] = email.Utils.formatdate()

    return message

class BestEffortSMTPMailer(SMTPMailer):
    """
    Try to send the message; if we fail, just log the error, and don't abort
    the transaction.
    """
    def send(self, fromaddr, toaddrs, message):
        try:
            super(BestEffortSMTPMailer, self).send(fromaddr, toaddrs, message)
        except:
            mail_logger.exception("Failed to send email message.")
            # TODO write message to the portal's `error_log`

def delivery_for_site(site):
    delivery = queryUtility(IMailDelivery, 'naaya-mail-delivery')
    if delivery is not None:
        return delivery

    elif site.mail_server_name and site.mail_server_port:
        from zope.sendmail.delivery import DirectMailDelivery
        site_mailer = BestEffortSMTPMailer(site.mail_server_name,
                                           site.mail_server_port)
        return DirectMailDelivery(site_mailer)

    else:
        return None

class _ImmediateDelivery(object):
    """
    Hack a queued message delivery to send the message immediately, and not
    wait for transaction finish; useful when sending error messages.
    """
    def __init__(self, delivery):
        self._d = delivery

    def send(self, fromaddr, toaddrs, message):
        message_id = self._d.newMessageId()
        email_message = create_plain_message(message)
        email_message['Message-Id'] = '<%s>' % message_id
        # make data_manager think it's being called by a transaction
        try:
            data_manager = self._d.createDataManager(fromaddr, toaddrs,
                                                     email_message)
        except TypeError:
            # backwards compat with zope.sendmail and repoze.sendmail < 2.0
            message_bytes = 'Message-Id: <%s>\n%s' % (message_id, message)
            data_manager = self._d.createDataManager(fromaddr, toaddrs,
                                                     message_bytes)
        data_manager.tpc_finish(None)

def configure_mail_queue():
    """
    Check if a mail queue path is configured; register a QueuedMailDelivery.
    """
    queue_path = os.environ.get('NAAYA_MAIL_QUEUE', None)
    if queue_path is None:
        return

    from zope.sendmail.interfaces import IMailDelivery
    try:
        from repoze.sendmail.delivery import QueuedMailDelivery
    except ImportError:
        from zope.sendmail.delivery import QueuedMailDelivery
    gsm = getGlobalSiteManager()
    gsm.registerUtility(QueuedMailDelivery(queue_path),
                        IMailDelivery, "naaya-mail-delivery")

    mail_logger.info("Mail queue: %r", queue_path)
