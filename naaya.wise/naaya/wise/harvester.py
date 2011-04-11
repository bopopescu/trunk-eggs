from urllib2 import urlopen
from lxml import etree

class WiseHarvester(object):

    def harvest_feed(self, feed):
        fp = urlopen(feed.get_feed_url())

        tree = etree.parse(fp)
        items = tree.xpath('/wcm/PressRelease')

        entries = []
        for item in items:
            keywords = [k.text for k in item.xpath('keywords/keyword')]
            if 'WATER' in keywords:
                entry = {}
                entry['author'] = ''
                entry['id'] = item.xpath('id')[0].text
                entry['modified'] = item.xpath('date')[0].text

                for content in item.xpath('language'):
                    if content.xpath('code')[0].text == 'EN':
                        entry['link'] = content.xpath('url')[0].text
                        entry['summary'] = content.xpath('description')[0].text
                        entry['title'] = content.xpath('title')[0].text
                        break
                entries.append(entry)
        return {
            'feed': {
                'link': feed.get_feed_url(),
                'title': feed.title_or_id(),
            },
            'status': fp.code,
            'version': fp.headers.getparam('content-type'),
            'encoding': fp.headers.getparam('charset'),
            'etag': None,
            'modified': fp.headers.getparam('date'),
            'entries': entries,
        }