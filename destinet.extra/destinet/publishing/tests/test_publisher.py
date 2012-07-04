from mock import Mock
import logging
from tempfile import NamedTemporaryFile

import transaction
from AccessControl.SecurityManagement import newSecurityManager, noSecurityManager
from AccessControl.User import UnrestrictedUser

from Products.Naaya.NyFolder import addNyFolder
from Products.Naaya.tests.NaayaTestCase import NaayaTestCase

from naaya.core.zope2util import path_in_site
from naaya.content.url.url_item import addNyURL
from naaya.content.pointer.pointer_item import NyPointer

import destinet.publishing
from destinet.publishing.DestinetPublisher import manage_addDestinetPublisher


def loginUnrestricted():
    """ """
    noSecurityManager()
    god = UnrestrictedUser('god', 'god', [], '')
    newSecurityManager(None, god)
    return god


class PublisherTestSuite(NaayaTestCase):

    def setUp(self):
        self.REQUEST = Mock()
        self.REQUEST.RESPONSE = Mock()
        self.redirect = None
        def save_redirect(url):
            self.redirect = url
        self.REQUEST.RESPONSE.redirect = save_redirect
        super(PublisherTestSuite, self).setUp()
        # Destinet setup
        addNyFolder(self.portal, 'topics')
        addNyFolder(self.portal.topics, 'atopic')
        addNyFolder(self.portal, 'who-who')
        addNyFolder(self.portal['who-who'], 'atarget_group')
        addNyFolder(self.portal, 'resources')
        addNyFolder(self.portal, 'market-place')
        addNyFolder(self.portal, 'News')
        addNyFolder(self.portal, 'events')
        addNyFolder(self.portal, 'countries')
        addNyFolder(self.portal.countries, 'georgia', title='Georgia')
        addNyFolder(self.portal.countries, 'southgeorgia', title='South Georgia')
        schema = self.portal.portal_schemas['NyURL']
        schema.addWidget('topics', widget_type='SelectMultiple', data_type='list')
        schema.addWidget('target-groups', widget_type='SelectMultiple', data_type='list')
        manage_addDestinetPublisher(self.portal)
        cat = self.portal.getCatalogTool()
        cat.addIndex('pointer', 'FieldIndex')
        # Logger setup for testing:
        logger = logging.getLogger(destinet.publishing.subscribers.__name__)
        self.logfile = NamedTemporaryFile()
        handler = logging.FileHandler(self.logfile.name)
        logger.addHandler(handler)

    def tearDown(self):
        self.logfile.close()

    def test_disseminate_url(self):
        addNyURL(self.portal.resources, id='url', title='url',
                 coverage='Georgia, Not Existing', topics=['atopic'],
                 url='http://eaudeweb.ro', contributor='simiamih')
        self.assertTrue(isinstance(getattr(self.portal.topics.atopic, 'url', None),
                                   NyPointer))
        self.assertTrue(isinstance(getattr(self.portal.countries.georgia,
                                           'url', None), NyPointer))
        self.assertEqual(getattr(self.portal.countries.southgeorgia,
                                           'url', None), None)

        log_content = self.logfile.read()
        self.assertTrue("Country 'Not Existing' not found in destinet countries"
                        in log_content)

    def test_cut_paste(self):
        loginUnrestricted()
        addNyURL(self.portal.resources, id='url', title='url',
                 coverage='Georgia, Not Existing', topics=['atopic'],
                 url='http://eaudeweb.ro', contributor='simiamih')
        transaction.commit()
        cp = self.portal.resources.manage_cutObjects('url')
        self.portal.countries.manage_pasteObjects(cp)
        ob = self.portal.countries.url
        new_path = path_in_site(ob)
        self.assertEqual(self.portal.topics.atopic.url.pointer, new_path)
        self.assertTrue(self.portal.countries.georgia.url.pointer, new_path)

    def test_approve_unapprove(self):
        addNyURL(self.portal.resources, id='url', title='url',
                 coverage='Georgia, Not Existing', topics=['atopic'],
                 url='http://eaudeweb.ro', contributor='simiamih')
        ob = self.portal.resources.url
        a_pointer = self.portal.countries.georgia.url
        self.assertEqual(ob.approved, a_pointer.approved)
        ob.approveThis(1, 'simiamih')
        self.assertEqual(ob.approved, a_pointer.approved)
