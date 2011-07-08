"""
ITranslationDomain utilities:
 * transitional NyLocalizerTranslator, for old edw-Localizer compliance
 * NyI18nTranslator
"""

from zope.interface import implements
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n import interpolate

try:
    from Products import Localizer
except ImportError:
    pass
else:
    from LocalizerWrapper import LocalizerWrapper

    class NyLocalizerTranslator(object):

        implements(ITranslationDomain)

        def translate(self, msgid, mapping=None, context=None, target_language=None,
                      default=None):
            try:
                site = context['PARENTS'][0].getSite()
                localizer = LocalizerWrapper(site)
            except KeyError, e:
                # malformed Request, probably we are in a mock/testing env.
                return msgid

            # TODO: set target_language if we want to move negotiation here
            return localizer.translate(msgid, mapping, context, target_language,
                                       default)


class NyI18nTranslator(object):

    implements(ITranslationDomain)

    def translate(self, msgid, mapping=None, context=None, target_language=None,
                  default=None):
        """
            Implementation of ITranslationDomain.translate using portal_i18n
        """
        site = context['PARENTS'][0].getSite()
        tool = site.getPortalI18n()
        if target_language is None:
            available = tool.get_lang_manager().getAvailableLanguages()
            target_language = tool.get_negotiator().getLanguage(available,
                                                                context)
        if default is not None:
            raw = tool.get_message_catalog().gettext(msgid, target_language,
                                             default=default)
        else:
            raw = tool.get_message_catalog().gettext(msgid, target_language)
        return interpolate(raw, mapping)
