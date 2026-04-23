def _real_extract(self, url):
        video_id = self._match_id(url)
        try:
            film_json = self._download_json(
                f'https://www.cinetecamilano.it/api/catalogo/{video_id}/?',
                video_id, headers={
                    'Referer': url,
                    'Authorization': try_get(self._get_cookies('https://www.cinetecamilano.it'), lambda x: f'Bearer {x["cnt-token"].value}') or '',
                })
        except ExtractorError as e:
            if ((isinstance(e.cause, HTTPError) and e.cause.status == 500)
                    or isinstance(e.cause, json.JSONDecodeError)):
                self.raise_login_required(method='cookies')
            raise
        if not film_json.get('success') or not film_json.get('archive'):
            raise ExtractorError('Video information not found')
        archive = film_json['archive']

        return {
            'id': video_id,
            'title': archive.get('title'),
            'description': strip_or_none(archive.get('description')),
            'duration': float_or_none(archive.get('duration'), invscale=60),
            'release_timestamp': parse_iso8601(archive.get('updated_at'), delimiter=' '),
            'modified_timestamp': parse_iso8601(archive.get('created_at'), delimiter=' '),
            'thumbnail': urljoin(url, try_get(archive, lambda x: x['thumb']['src'].replace('/public/', '/storage/'))),
            'formats': self._extract_m3u8_formats(
                urljoin(url, traverse_obj(archive, ('drm', 'hls'))), video_id, 'mp4'),
        }