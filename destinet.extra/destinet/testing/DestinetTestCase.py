from Products.Naaya.NyFolder import addNyFolder
from Products.Naaya.tests.NaayaTestCase import NaayaTestCase
from Products.EnviroWindows.EnviroWindowsSite import manage_addEnviroWindowsSite
from Products.Naaya.tests.NaayaFunctionalTestCase import TwillMixin
from naaya.component import bundles

from destinet.publishing.DestinetPublisher import manage_addDestinetPublisher


class DestinetTestCase(NaayaTestCase):

    def setUp(self):
        super(DestinetTestCase, self).setUp()
        # EW setup
        portal_id = self.portal.getId()
        self.app._delObject(portal_id)
        portal_id = 'demo-design'
        manage_addEnviroWindowsSite(self.app, portal_id)
        self.portal = self.app[portal_id]
        # Destinet setup
        addNyFolder(self.portal, 'topics')
        addNyFolder(self.portal.topics, 'atopic')
        addNyFolder(self.portal, 'who-who')
        addNyFolder(self.portal['who-who'], 'atarget_group')
        addNyFolder(self.portal['who-who'], 'destinet-users')
        addNyFolder(self.portal, 'resources')
        addNyFolder(self.portal, 'market-place')
        addNyFolder(self.portal, 'News')
        addNyFolder(self.portal, 'events')
        addNyFolder(self.portal, 'countries')
        addNyFolder(self.portal.countries, 'georgia', title='Georgia')
        addNyFolder(self.portal.countries, 'southgeorgia', title='South Georgia')
        schemas = [self.portal.portal_schemas[x] for x in ('NyURL', 'NyContact')]
        for schema in schemas:
            schema.addWidget('topics', widget_type='SelectMultiple', data_type='list')
            schema.addWidget('target-groups', widget_type='SelectMultiple', data_type='list')
            schema.addWidget('administrative_level', widget_type='Select', data_type='str')
            schema.addWidget('landscape_type', widget_type='SelectMultiple', data_type='list')
        
        manage_addDestinetPublisher(self.portal)
        cat = self.portal.getCatalogTool()
        cat.addIndex('pointer', 'FieldIndex')
        # set bundle
        naaya_b = bundles.get("Naaya")
        ew_b = bundles.get("EW")
        bundle = bundles.get("DESTINET-demo-design")
        ew_b.set_parent(naaya_b)
        bundle.set_parent(ew_b)
        self.portal.set_bundle(bundle)


class DestinetFunctionalTestCase(DestinetTestCase, TwillMixin):
    """
    Functional test case for Destinet -
    use Twill (http://twill.idyll.org/) for client-side tests

    """

    def setUp(self):
        super(DestinetFunctionalTestCase, self).setUp()
        self.install_twill()
        #This is needed for absolute_url
        self.portal.REQUEST.setServerURL('http', 'localhost')

    def tearDown(self):
        super(DestinetFunctionalTestCase, self).tearDown()
        self.remove_twill()
