import transaction
from webob import Request
from Products.Naaya.tests.NaayaTestCase import NaayaTestCase
from Products.Naaya.NyFolder import addNyFolder
from naaya.core.testutils import parse_html, css


class _CommonContentTest(NaayaTestCase):
    """
    Common tests for Naaya content objects

    `ob`
        Object under test. Created by `setUp`.
    """

    # TODO naaya.content.base.tests.testContentTypeConformance should be
    # refactored to use the _CommonContentTest pattern

    def add_object(self, parent):
        """ Create and return an instance of the class to be tested. """
        raise NotImplementedError

    def setUp(self):
        addNyFolder(self.portal, 'box', contributor='contributor', submitted=1)
        self.ob = self.add_object(self.portal['box'])
        transaction.commit()

    def _get_h1_icon_src(self):
        request = Request.blank(self.ob.absolute_url())
        page = parse_html(request.get_response(self.wsgi_request).body)
        return css(page, 'h1 img')[0].attrib['src']

    def _get_folder_icon_src(self):
        request = Request.blank(self.ob.aq_parent.absolute_url())
        page = parse_html(request.get_response(self.wsgi_request).body)
        for tr in css(page, 'table#folderfile_list tr'):
            links = [a.attrib['href'] for a in css(tr, 'td a')]
            if self.ob.absolute_url() in links:
                break
        else:
            self.fail("Link to object %r not found" % self.ob)

        return css(tr, 'td img')[0].attrib['src']

    def test_icon(self):
        self.assertEqual(self._get_h1_icon_src(), self.ob.icon)
        #TODO self.assertEqual(self._get_folder_icon_src(), self.ob.icon)

        self.ob.approveThis(0, None)
        transaction.commit()
        self.assertEqual(self._get_h1_icon_src(), self.ob.icon_marked)
        #TODO self.assertEqual(self._get_folder_icon_src(), self.ob.icon_marked)
