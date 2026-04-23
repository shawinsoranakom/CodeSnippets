def _entries(self, playlist_id, *args, **kwargs):
        next_page_url = None
        for pagenum in itertools.count(1):
            page = self._download_json(
                next_page_url or self._next_page_url(
                    pagenum, playlist_id, *args, **kwargs),
                playlist_id, f'Downloading page {pagenum}')

            results = page.get('results')
            if not results or not isinstance(results, list):
                break

            for result in results:
                video_url = url_or_none(result.get('video_url'))
                if not video_url:
                    continue
                entry = self._extract_info(result, require_title=False)
                entry.update({
                    '_type': 'url',
                    'url': video_url,
                    'ie_key': RutubeIE.ie_key(),
                })
                yield entry

            next_page_url = page.get('next')
            if not next_page_url or not page.get('has_next'):
                break