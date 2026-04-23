def _extract_item(self, item, fatal):
        item_id = item['id']
        title = item.get('name') or item['title']

        formats = []
        for k, v in (item.get('source') or {}).items():
            if not v:
                continue
            if k in ('mp4', 'hls'):
                for res, video_url in v.items():
                    if not video_url:
                        continue
                    if k == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            video_url, item_id, 'mp4',
                            'm3u8_native', m3u8_id=k, fatal=False))
                    elif k == 'mp4':
                        formats.append({
                            'format_id': 'mp4-' + res,
                            'url': video_url,
                            'height': int_or_none(self._search_regex(
                                r'^(\d+)p', res, 'resolution', default=None)),
                        })
            else:
                formats.append({
                    'ext': 'mp3',
                    'format_id': k,
                    'tbr': int_or_none(k),
                    'url': self._proto_relative_url(v),
                    'vcodec': 'none',
                })
        if not formats:
            if not fatal:
                return
            msg = item['msg']
            if msg == 'Sorry, this content is not available in your country.':
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            raise ExtractorError(msg, expected=True)
        self._sort_formats(formats)

        subtitles = None
        lyric = item.get('lyric')
        if lyric:
            subtitles = {
                'origin': [{
                    'url': lyric,
                }],
            }

        album = item.get('album') or {}

        return {
            'id': item_id,
            'title': title,
            'formats': formats,
            'thumbnail': item.get('thumbnail'),
            'subtitles': subtitles,
            'duration': int_or_none(item.get('duration')),
            'track': title,
            'artist': item.get('artists_names'),
            'album': album.get('name') or album.get('title'),
            'album_artist': album.get('artists_names'),
        }