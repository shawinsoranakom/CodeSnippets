def crawl(self, url, seen=None, msg=''):
        if seen is None:
            seen = set()

        url_slug = self.clean_url(url)

        if url_slug in seen:
            return seen
        seen.add(url_slug)

        _logger.info("%s %s", msg, url)
        r = self.url_open(url, allow_redirects=False)
        if r.status_code in (301, 302, 303):
            # check local redirect to avoid fetch externals pages
            new_url = r.headers.get('Location')
            current_url = r.url
            if urls.url_parse(new_url).netloc != urls.url_parse(current_url).netloc:
                return seen
            r = self.url_open(new_url)

        code = r.status_code
        self.assertIn(code, range(200, 300), "%s Fetching %s returned error response (%d)" % (msg, url, code))

        if r.headers['Content-Type'].startswith('text/html'):
            doc = lxml.html.fromstring(r.content)
            for link in doc.xpath('//a[@href]'):
                href = link.get('href')

                parts = urls.url_parse(href)
                # href with any fragment removed
                href = parts.replace(fragment='').to_url()

                # FIXME: handle relative link (not parts.path.startswith /)
                if parts.netloc or \
                    not parts.path.startswith('/') or \
                    parts.path == '/odoo' or\
                    parts.path.startswith('/web/') or \
                    parts.path.startswith('/en/') or \
                   (parts.scheme and parts.scheme not in ('http', 'https')):
                    continue

                self.crawl(href, seen, msg)
        return seen