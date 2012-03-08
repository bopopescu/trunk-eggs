1.0.14 (unreleased)
-------------------
* ready for zodbupdate [simiamih]
* Fix for messages with new_line characters [dumitval]

1.0.13 (2012-03-07)
-------------------
* Fix for Google translate suggestion in portals with many languages [dumitval]

1.0.12 (2012-03-07)
-------------------
* debug handler no longer brakes functional tests [simiamih]
* bugfix: skey must be int, regardless of `skey` lang existance [simiamih]

1.0.11 (2012-02-01)
------------------
* Debugging code to find sources of spurious messages [moregale]
* Remove annoying log warnings [moregale]

1.0.10 (2012-01-13)
------------------
* Added default value when calling gettext [dumitval]
* override views config for Five: set different i18n_domain [simiamih]

1.0.9 (2012-01-06)
------------------
* spreadsheet_import/export works [simiamih]

1.0.8 (2011-12-22)
------------------
* strips and collapses whitespaces in message translations [simiamih]

1.0.7 (2011-11-08)
------------------
* bufix: setting default lang or del. languages when custom order is
  specified #739 [simiamih]

1.0.6 (2011-11-03)
------------------
* feature: fallback for translation utility - identity translation when
  not in INySite portal context [simiamih]

1.0.5 (2011-10-20)
------------------
* bugfix: fallback lang on localprops when lang is specified
  in params [simiamih]

1.0.4 (2011-10-19)
------------------
* feature: return en translation when default lang in site is not en,
  but object has translation only for en [simiamih]

1.0.3 (2011-10-13)
------------------
* feature: languages display order is customizable [simiamih]

1.0.2 (2011-10-10)
------------------
* update script for cleaning empty translations on local
  props

1.0.1 (2011-10-07)
------------------
* _p_changed = 1 for deleting contenttype property on site

1.0 (2011-10-06)
----------------
* Fully functional version - now translating templates, messages, local
  properties and linked with Naaya administration
* includes migration script from :mod:`Products.Localizer`

0.1.2 (2011-06-14)
-------------------
* Renamed get_catalog to get_message_catalog

0.1 (2011-06-10)
-------------------
* First numbered version
* TODO: test local properties, importing language files (po, tmx, xliff)
* TODO: several fixes and update script from old localizer
