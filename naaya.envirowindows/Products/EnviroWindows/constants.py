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
# Authors:
#
# Alexandru Ghica
# Cornel Nitu
# Gabriel Agu
# Miruna Badescu

#Python imports

#Zope imports

#Product imports
import Globals


#portal related
ENVIROWINDOWS_PRODUCT_NAME =    'EnviroWindows'
ENVIROWINDOWS_PRODUCT_PATH =    Globals.package_home(globals())
PERMISSION_ADD_EWSITE =         'EnviroWindows - Add EnviroWindows Site objects'
METATYPE_ENVIROWINDOWSSITE =    'EnviroWindows Site'

#deafault content related
ID_RDFCALENDAR =        'portal_rdfcalendar'
TITLE_RDFCALENDAR =     'RDF Calendar'

ID_LINKCHECKER = 'LinkChecker'
TITLE_LINKCHECKER = 'URL checker'