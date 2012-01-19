from mock import Mock

from Products.Naaya.NyFolder import addNyFolder
from Products.Naaya.tests.NaayaTestCase import NaayaTestCase

from naaya.content.url.url_item import addNyURL
from naaya.content.pointer.pointer_item import NyPointer

from destinet.publishing.DestinetPublisher import manage_addDestinetPublisher

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
        addNyFolder(self.portal.countries, 'denmark', title='Denmark')
        schema = self.portal.portal_schemas['NyURL']
        schema.addWidget('topics', widget_type='SelectMultiple', data_type='list')
        schema.addWidget('target-groups', widget_type='SelectMultiple', data_type='list')
        manage_addDestinetPublisher(self.portal)

    def test_disseminate_url(self):
        addNyURL(self.portal.resources, id='url', title='url',
                 coverage='Denmark', topics=['atopic'],
                 url='http://eaudeweb.ro', contributor='simiamih')
        self.assertTrue(isinstance(getattr(self.portal.topics.atopic, 'url', None),
                                   NyPointer))
        self.assertTrue(isinstance(getattr(self.portal.countries.denmark,
                                           'url', None),
                                   NyPointer))
