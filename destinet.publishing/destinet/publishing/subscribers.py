from OFS.interfaces import IObjectWillBeAddedEvent

from naaya.core.zope2util import is_descendant_of, path_in_site, ofs_path
from naaya.content.pointer.pointer_item import addNyPointer
from naaya.content.event.event_item import NyEvent
from naaya.content.news.news_item import NyNews
from naaya.content.contact.contact_item import NyContact
from naaya.content.url.url_item import NyURL
from naaya.content.file.file_item import NyFile_extfile
from naaya.content.mediafile.mediafile_item import NyMediaFile_extfile
from Products.NaayaContent.NyPublication.NyPublication import NyPublication

def get_countries(ob):
    """
    Extracts coverage from ob, iterates countries and returns
    nyfolders of them in `countries` location (creates them if missing)

    """
    ret = []
    site = ob.getSite()
    cat = site.getCatalogTool()
    filters = {'title': '', 'path': ofs_path(site.countries),
               'meta_type': 'Naaya Folder'}
    coverage = list(set(getattr(ob, 'coverage', u'').strip(',').split(',')))
    for country_item in coverage:
        country = country_item.strip()
        if country:
            filters['title'] = country
            bz = cat.search(filters)
            for brain in bz:
                ret.append(brain.getObject())
    return ret

def place_pointers(ob, exclude=[]):
    """ Ads pointers to ob in target_groups and topics """
    props = {
        'title': ob.title,
        'description': getattr(ob, 'description', ''),
        'topics': ob.__dict__.get('topics', []),
        'target-groups': ob.__dict__.get('topics', []),
        'geo_location.lat': '',
        'geo_location.lon': '',
        'geo_location.address': '',
        'geo_type': getattr(ob, 'geo_type', ''),
        'coverage': ob.__dict__.get('coverage', ''),
        'keywords': ob.__dict__.get('keywords', ''),
        'sortorder': getattr(ob, 'sortorder', ''),
        'redirect': True,
        'pointer': path_in_site(ob)
    }
    if ob.geo_location:
        if ob.geo_location.lat:
            props['geo_location.lat'] = unicode(ob.geo_location.lat)
        if ob.geo_location.lon:
            props['geo_location.lon'] = unicode(ob.geo_location.lon)
        if ob.geo_location.address:
            props['geo_location.address'] = ob.geo_location.address
    site = ob.getSite()
    target_groups = ob.__dict__.get("target-groups", [])
    topics = ob.__dict__.get("topics", [])
    locations = [] # pointer locations
    if 'target-groups' not in exclude and isinstance(target_groups, list):
        for tgrup in target_groups:
            locations.append(site.unrestrictedTraverse("who-who/%s" % str(tgrup)))
    if isinstance(topics, list):
        for topic in topics:
            locations.append(site.unrestrictedTraverse("topics/%s" % str(topic)))
    locations.extend(get_countries(ob))
    for loc in locations:
        if not props['sortorder']:
            props['sortorder'] = '200'
        p_id = addNyPointer(loc, '', contributor=ob.contributor, **props)
        pointer = getattr(loc, p_id)
        if pointer:
            if ob.approved:
                pointer.approveThis(1, ob.contributor)
            else:
                pointer.approveThis(0, None)


def handle_add_content(event):
    """
    Test whether this requires adding pointers and perform the action

    """
    obj = event.context
    site = obj.getSite()
    resources = site.resources
    news = site.News
    events = site.events
    market_place = getattr(site, 'market-place')
    who_who = getattr(site, 'who-who')
    if ((isinstance(obj, NyEvent) and is_descendant_of(obj, events)) or
        (isinstance(obj, NyNews) and is_descendant_of(obj, news)) or
        (isinstance(obj, (NyFile_extfile, NyMediaFile_extfile, NyURL, NyPublication))
          and is_descendant_of(obj, resources))
       ):
        pass
