def entries(page_url, html=None):
            for page in itertools.count(1):
                if not html:
                    html = self._download_webpage(
                        page_url, pl_id, note='Downloading page %d' % (page, ),
                        fatal=False) or ''
                for u in self._urls(html):
                    yield u
                next_page = get_element_by_class('pagination-next', html) or ''
                if next_page:
                    # member list page
                    next_page = urljoin(url, self._search_regex(
                        r'''<a\b[^>]+\bhref\s*=\s*("|')(?P<url>(?!#)(?:(?!\1).)+)''',
                        next_page, 'next page link', group='url', default=None))
                # in case a member page should have pagination-next with empty link, not just `else:`
                if next_page is None:
                    # playlist page
                    parsed_url = compat_urlparse.urlparse(page_url)
                    base_path, num = parsed_url.path.rsplit('/', 1)
                    num = int_or_none(num)
                    if num is None:
                        base_path, num = parsed_url.path.rstrip('/'), 1
                    parsed_url = parsed_url._replace(path=base_path + ('/%d' % (num + 1, )))
                    next_page = compat_urlparse.urlunparse(parsed_url)
                    if page_url == next_page:
                        next_page = None
                if not next_page:
                    break
                page_url, html = next_page, None