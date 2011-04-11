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
# Alin Voinea, Eau de Web
from unittest import TestSuite, makeSuite
from naaya.content.semide.textlaws.semtextlaws_item import addNySemTextLaws
from Products.Naaya.tests import NaayaTestCase

class NaayaContentTestCase(NaayaTestCase.NaayaTestCase):
    """ TestCase for NaayaContent object
    """
    def afterSetUp(self):
        self.login()
        
    def beforeTearDown(self):
        self.logout()

    def test_main(self):
        """ Add, Find, Edit and Delete Naaya Semide Text of Laws """
        addNySemTextLaws(self._portal().info, id='doc1', title='doc1', lang='en', submitted=1)
        addNySemTextLaws(self._portal().info, id='doc1_fr', title='doc1_fr', lang='fr', submitted=1)
        
        docs = self._portal().getCatalogedObjectsCheckView(meta_type=['Naaya Semide Text of Laws'])
        
        #Get added NyDocument
        for x in docs:
            if x.getLocalProperty('title', 'en') == 'doc1':
                meta = x
            if x.getLocalProperty('title', 'fr') == 'doc1_fr':
                meta_fr = x
        
        self.assertEqual(meta.getLocalProperty('title', 'en'), 'doc1')
        self.assertEqual(meta_fr.getLocalProperty('title', 'fr'), 'doc1_fr')
        
        #Change NyDocument title
        meta.saveProperties(title='doc1_edited', lang='en')
        meta_fr.saveProperties(title='doc1_fr_edited', lang='fr')
        
        self.assertEqual(meta.getLocalProperty('title', 'en'), 'doc1_edited')
        self.assertEqual(meta_fr.getLocalProperty('title', 'fr'), 'doc1_fr_edited')
        
        #delete NyDocument
        self._portal().info.manage_delObjects([meta.id])
        self._portal().info.manage_delObjects([meta_fr.id])
        
        brains = self._portal().getCatalogedObjectsCheckView(meta_type=['Naaya Semide Text of Laws'])
        self.assertEqual(len(brains), 0)

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(NaayaContentTestCase))
    return suite