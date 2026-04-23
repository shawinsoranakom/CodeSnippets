def _entries(self, url, playlist_id):
        # Per the SoundCloud documentation, the maximum limit for a linked partitioning query is 200.
        # https://developers.soundcloud.com/blog/offset-pagination-deprecated
        query = {
            'limit': 200,
            'linked_partitioning': '1',
            'offset': 0,
        }

        for i in itertools.count():
            for retry in self.RetryManager():
                try:
                    response = self._call_api(
                        url, playlist_id, query=query, headers=self._HEADERS,
                        note=f'Downloading track page {i + 1}',
                        # See: https://github.com/yt-dlp/yt-dlp/issues/15660
                        impersonate=self._browser_impersonate_target)
                    break
                except ExtractorError as e:
                    # Downloading page may result in intermittent 502 HTTP error
                    # See https://github.com/yt-dlp/yt-dlp/issues/872
                    if not isinstance(e.cause, HTTPError) or e.cause.status != 502:
                        raise
                    retry.error = e
                    continue

            def resolve_entry(*candidates):
                for cand in candidates:
                    if not isinstance(cand, dict):
                        continue
                    permalink_url = url_or_none(cand.get('permalink_url'))
                    if permalink_url:
                        return self.url_result(
                            permalink_url,
                            SoundcloudIE.ie_key() if SoundcloudIE.suitable(permalink_url) else None,
                            str_or_none(cand.get('id')), cand.get('title'))

            for e in response['collection'] or []:
                yield resolve_entry(e, e.get('track'), e.get('playlist'))

            url = response.get('next_href')
            if not url:
                break
            query.pop('offset', None)