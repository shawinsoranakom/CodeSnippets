def yield_pages(url, html=html, page_num=page_num):
            fatal = not html
            for pnum in itertools.count(start=page_num or 1):
                if not html:
                    html = self._download_webpage(
                        url, pl_id, note='Downloading page %d' % pnum,
                        fatal=fatal)
                if not html:
                    break
                fatal = False
                yield (url, html, pnum)
                # explicit page: extract just that page
                if page_num is not None:
                    break
                next_url = self._get_next_url(url, pl_id, html)
                if not next_url or next_url == url:
                    break
                url, html = next_url, None