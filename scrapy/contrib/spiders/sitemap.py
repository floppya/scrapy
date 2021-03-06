import re

from scrapy.spider import BaseSpider
from scrapy.http import Request, XmlResponse
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy import log

class SitemapSpider(BaseSpider):

    sitemap_urls = ()
    sitemap_rules = [('', 'parse')]
    sitemap_follow = ['']

    def __init__(self, *a, **kw):
        super(SitemapSpider, self).__init__(*a, **kw)
        self._cbs = []
        for r, c in self.sitemap_rules:
            if isinstance(c, basestring):
                c = getattr(self, c)
            self._cbs.append((regex(r), c))
        self._follow = [regex(x) for x in self.sitemap_follow]

    def start_requests(self):
        return [Request(x, callback=self._parse_sitemap) for x in self.sitemap_urls]

    def _parse_sitemap(self, response):
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.body):
                yield Request(url, callback=self._parse_sitemap)
        else:
            if not isinstance(response, XmlResponse):
                log.msg("Ignoring non-XML sitemap: %s" % response, log.WARNING)
                return
            s = Sitemap(response.body)
            if s.type == 'sitemapindex':
                for loc in iterloc(s):
                    if any(x.search(loc) for x in self._follow):
                        yield Request(loc, callback=self._parse_sitemap)
            elif s.type == 'urlset':
                for loc in iterloc(s):
                    for r, c in self._cbs:
                        if r.search(loc):
                            yield Request(loc, callback=c)
                            break


def regex(x):
    if isinstance(x, basestring):
        return re.compile(x)
    return x

def iterloc(it):
    for d in it:
        yield d['loc']
