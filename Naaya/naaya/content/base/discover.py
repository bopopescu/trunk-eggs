
import os
import sys
import re
from copy import copy

from App.ImageFile import ImageFile
import zLOG
from zope.component import getUtility
from meta import INaayaContent

from constants import *
from Products.NaayaBase.NyValidation import NyValidation


def _get_content_types():
    """ make sure _discover_content_types has been run, and return its output """
    nyct = getUtility(INaayaContent)
    return {
            'content': nyct.contents,
            'constants': nyct.constants,
            'misc_': nyct.misc,
        }

def get_constant(name):
    """ returns a constant of the form METATYPE_*** or PERMISSION_ADD_*** """
    return _get_content_types()['constants'][name]

def get_pluggable_content():
    return _get_content_types()['content']

def initialize(context):
    """ """

    #register classes
    for x in _get_content_types()['content'].values():
        context.registerClass(
                x['_class'],
                permission=x['permission'],
                #constructors=(getattr(x['_module'], 'manage_add%s_html' % (x['module'],)),
                #              getattr(x['_module'], 'add%s' % (x['module'],))),
                constructors=x['constructors'],
                icon=x['icon'],
                visibility=None)

#misc_ = _get_content_types()['misc_']

## TODO: we still have global constants for the content types, for backwards compatibility
#for cname, cvalue in _get_content_types()['constants'].iteritems():
#    exec('%s = "%s"' % (cname, cvalue))


