#Python imports
from base64 import urlsafe_b64encode
from random import randrange

#Zope imports
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Persistence import Persistent
from BTrees.OOBTree import OOBTree
from AccessControl.User import BasicUserFolder, SimpleUser
from AccessControl.Permissions import view

#Naaya imports
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile

#meeting imports
from naaya.content.meeting import PARTICIPANT_ROLE
from naaya.content.meeting import PERMISSION_PARTICIPATE_IN_MEETING, PERMISSION_ADMIN_MEETING
from utils import getUserFullName, getUserEmail, getUserOrganization, getUserPhoneNumber

class Subscriptions(SimpleItem):
    security = ClassSecurityInfo()

    title = "Meeting registrations"

    def __init__(self, id):
        """ """
        super(SimpleItem, self).__init__(id)
        self.id = id
        self._signups = OOBTree()
        self._account_subscriptions = OOBTree()

    security.declarePublic('getMeeting')
    def getMeeting(self):
        return self.aq_parent.aq_parent

    def _validate_signup(self, form):
        """ """
        formdata = {}
        formerrors = {}

        keys = ('first_name', 'last_name', 'email', 'organization', 'phone')
        formdata = dict( (key, form.get(key, '')) for key in keys )
        for key in formdata:
            if formdata[key] == '':
                formerrors[key] = 'This field is mandatory'

        if formerrors == {}:
            if formdata['email'].count('@') != 1:
                formerrors['email'] = 'An email address must contain a single @'

        if formerrors == {}:
            formerrors = None
        return formdata, formerrors

    def _add_signup(self, formdata):
        """ """
        meeting = self.getMeeting()
        key = random_key()
        name = formdata['first_name'] + ' ' + formdata['last_name']
        email = formdata['email']
        organization = formdata['organization']
        phone = formdata['phone']

        signup = SignUp(key, name, email, organization, phone)

        self._signups.insert(key, signup)

        if meeting.auto_register:
            self._accept_signup(key)

        email_sender = self.getMeeting().getEmailSender()
        email_sender.send_signup_email(signup)

    security.declareProtected(view, 'signup')
    def signup(self, REQUEST):
        """ """
        meeting = self.getMeeting()
        if not meeting.allow_register:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + '/subscription_not_allowed')

        if REQUEST.REQUEST_METHOD == 'GET':
            return self.getFormsTool().getContent({'here': self},
                                 'naaya.content.meeting.subscription_signup')

        if REQUEST.REQUEST_METHOD == 'POST':
            formdata, formerrors = self._validate_signup(REQUEST.form)

            #check Captcha/reCaptcha
            if not self.checkPermissionSkipCaptcha():
                contact_word = REQUEST.form.get('contact_word', '')
                captcha_validator = self.validateCaptcha(contact_word, REQUEST)
                if captcha_validator:
                    if formerrors is None:
                        formerrors = {}
                    formerrors['captcha'] = captcha_validator

            if formerrors is not None:
                return self.getFormsTool().getContent({'here': self,
                                                     'formdata': formdata,
                                                     'formerrors': formerrors},
                                         'naaya.content.meeting.subscription_signup')
            else:
                self._add_signup(formdata)
                REQUEST.RESPONSE.redirect(self.absolute_url() + '/signup_successful')

    security.declareProtected(view, 'signup_successful')
    def signup_successful(self, REQUEST):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'naaya.content.meeting.subscription_signup_successful')

    security.declareProtected(view, 'subscribe')
    def subscribe(self, REQUEST):
        """ """
        meeting = self.getMeeting()
        if not meeting.allow_register:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + '/subscription_not_allowed')

        return self.getFormsTool().getContent({'here': self}, 'naaya.content.meeting.subscription_subscribe')

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'getSignups')
    def getSignups(self):
        """ """
        return self._signups.itervalues()

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'getSignup')
    def getSignup(self, key):
        """ """
        return self._signups.get(key, None)

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'index_html')
    def index_html(self, REQUEST):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'naaya.content.meeting.subscription_index')

    def _accept_signup(self, key):
        """ """
        meeting = self.getMeeting()
        meeting.getParticipants()._set_attendee(key, PARTICIPANT_ROLE)
        signup = self._signups[key]
        signup.accepted = 'accepted'

        email_sender = meeting.getEmailSender()
        result = email_sender.send_signup_accepted_email(signup)

    def _reject_signup(self, key):
        """ """
        meeting = self.getMeeting()
        signup = self._signups[key]
        signup.accepted = 'rejected'

        participants = meeting.getParticipants()
        if key in participants._get_attendees():
            participants._del_attendee(key)

        email_sender = meeting.getEmailSender()
        result = email_sender.send_signup_rejected_email(signup)

    def _delete_signup(self, key):
        """ """
        meeting = self.getMeeting()
        signup = self._signups.pop(key, None)
        if signup is None:
            return

        participants = meeting.getParticipants()
        if key in participants._get_attendees():
            participants._del_attendee(key)

        email_sender = meeting.getEmailSender()
        result = email_sender.send_signup_rejected_email(signup)

    def _is_signup(self, key):
        """ """
        return self._signups.has_key(key) and self._signups[key].accepted == 'accepted'

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'manageSignups')
    def manageSignups(self, REQUEST):
        """ """
        keys = REQUEST.form.get('keys', [])
        assert isinstance(keys, list)
        if 'accept' in REQUEST.form:
            for key in keys:
                self._accept_signup(key)
        elif 'reject' in REQUEST.form:
            for key in keys:
                self._reject_signup(key)
        elif 'delete' in REQUEST.form:
            for key in keys:
                self._delete_signup(key)

        return REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declarePublic('welcome')
    def welcome(self, REQUEST):
        """ """
        if 'logout' in REQUEST.form:
            REQUEST.SESSION['nymt-current-key'] = None
            return REQUEST.RESPONSE.redirect(self.getMeeting().absolute_url())

        key = REQUEST.get('key', None)
        signup = self.getSignup(key)
        if self._is_signup(key):
            REQUEST.SESSION['nymt-current-key'] = key

        return self.getFormsTool().getContent({'here': self,
                                                'signup': signup},
                                         'naaya.content.meeting.subscription_welcome')

    def _add_account_subscription(self, uid):
        """ """
        site = self.getSite()
        meeting = self.getMeeting()
        name = getUserFullName(site, uid)
        email = getUserEmail(site, uid)
        organization = getUserOrganization(site, uid)
        phone = getUserPhoneNumber(site, uid)

        account_subscription = AccountSubscription(uid, name, email, organization, phone)

        self._account_subscriptions.insert(uid, account_subscription)

        if meeting.auto_register:
            self._accept_account_subscription(uid)

        email_sender = self.getMeeting().getEmailSender()
        email_sender.send_account_subscription_email(account_subscription)

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'update_account_subscription')
    def update_account_subscription(self, uid):
        """ """
        site = self.getSite()
        name = getUserFullName(site, uid)
        email = getUserEmail(site, uid)
        organization = getUserOrganization(site, uid)
        phone = getUserPhoneNumber(site, uid)

        account_subscription = AccountSubscription(uid, name, email, organization, phone)

        self._account_subscriptions.update({uid: account_subscription})

    security.declareProtected(view, 'subscribe_account')
    def subscribe_account(self, REQUEST):
        """ """
        meeting = self.getMeeting()
        if not meeting.allow_register:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + '/subscription_not_allowed')

        self._add_account_subscription(REQUEST.AUTHENTICATED_USER.getId())
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/subscribe_account_successful')

    security.declareProtected(view, 'subscribe_account_successful')
    def subscribe_account_successful(self, REQUEST):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'naaya.content.meeting.subscription_subscribe_successful')

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'getAccountSubscriptions')
    def getAccountSubscriptions(self):
        """ """
        return self._account_subscriptions.itervalues()

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'getAccountSubscription')
    def getAccountSubscription(self, uid):
        """ """
        return self._account_subscriptions.get(uid, None)

    def _is_account_subscription(self, uid):
        """ """
        return self._account_subscriptions.has_key(uid) and self._account_subscriptions[uid].accepted == 'accepted'

    security.declareProtected(PERMISSION_ADMIN_MEETING, 'manageSignups')
    def manageAccountSubscriptions(self, REQUEST):
        """ """
        uids = REQUEST.form.get('uids', [])
        assert isinstance(uids, list)
        if 'accept' in REQUEST.form:
            for uid in uids:
                self._accept_account_subscription(uid)
        elif 'reject' in REQUEST.form:
            for uid in uids:
                self._reject_account_subscription(uid)
        elif 'delete' in REQUEST.form:
            for uid in uids:
                self._delete_account_subscription(uid)

        return REQUEST.RESPONSE.redirect(self.absolute_url())

    def _accept_account_subscription(self, uid):
        """ """
        meeting = self.getMeeting()
        meeting.getParticipants()._set_attendee(uid, PARTICIPANT_ROLE)
        account_subscription = self._account_subscriptions[uid]
        account_subscription.accepted = 'accepted'

        email_sender = meeting.getEmailSender()
        result = email_sender.send_account_subscription_accepted_email(account_subscription)

    def _reject_account_subscription(self, uid):
        """ """
        meeting = self.getMeeting()
        account_subscription = self._account_subscriptions[uid]
        account_subscription.accepted = 'rejected'

        participants = meeting.getParticipants()
        if uid in participants._get_attendees():
            participants._del_attendee(uid)

        email_sender = meeting.getEmailSender()
        result = email_sender.send_account_subscription_rejected_email(account_subscription)

    def _delete_account_subscription(self, uid):
        """ """
        meeting = self.getMeeting()
        account_subscription = self._account_subscriptions.pop(uid, None)
        if account_subscription is None:
            return

        participants = meeting.getParticipants()
        if uid in participants._get_attendees():
            participants._del_attendee(uid)

        email_sender = meeting.getEmailSender()
        result = email_sender.send_account_subscription_rejected_email(account_subscription)

    security.declareProtected(view, 'subscription_not_allowed')
    def subscription_not_allowed(self, REQUEST):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'naaya.content.meeting.subscription_not_allowed')


InitializeClass(Subscriptions)

class SignUp(Persistent):
    def __init__(self, key, name, email, organization, phone):
        self.key = key
        self.name = name
        self.email = email
        self.organization = organization
        self.phone = phone
        self.accepted = 'new'

class AccountSubscription(Persistent):
    def __init__(self, uid, name, email, organization, phone):
        self.uid = uid
        self.name = name
        self.email = email
        self.organization = organization
        self.phone = phone
        self.accepted = 'new'

class SignupUsersTool(BasicUserFolder):
    def getMeeting(self):
        return self.aq_parent

    def authenticate(self, name, password, REQUEST):
        participants = self.getMeeting().getParticipants()
        subscriptions = participants.getSubscriptions()

        key = REQUEST.SESSION.get('nymt-current-key', None)
        if subscriptions._is_signup(key):
            role = participants._get_attendees()[key]
            return SimpleUser('signup:' + key, '', (role,), [])
        else:
            return None

NaayaPageTemplateFile('zpt/subscription_subscribe', globals(),
        'naaya.content.meeting.subscription_subscribe')
NaayaPageTemplateFile('zpt/subscription_subscribe_successful', globals(),
        'naaya.content.meeting.subscription_subscribe_successful')
NaayaPageTemplateFile('zpt/subscription_signup', globals(),
        'naaya.content.meeting.subscription_signup')
NaayaPageTemplateFile('zpt/subscription_signup_successful', globals(),
        'naaya.content.meeting.subscription_signup_successful')
NaayaPageTemplateFile('zpt/subscription_index', globals(),
        'naaya.content.meeting.subscription_index')
NaayaPageTemplateFile('zpt/subscription_welcome', globals(),
        'naaya.content.meeting.subscription_welcome')
NaayaPageTemplateFile('zpt/subscription_not_allowed', globals(),
        'naaya.content.meeting.subscription_not_allowed')

def random_key():
    """ generate a 120-bit random key, expressed as 20 base64 characters """
    return urlsafe_b64encode(''.join(chr(randrange(256)) for i in xrange(15)))
