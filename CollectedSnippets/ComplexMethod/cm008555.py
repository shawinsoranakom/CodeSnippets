def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json(
            f'https://amara.org/api/videos/{video_id}/',
            video_id, query={'format': 'json'})
        title = meta['title']
        video_url = meta['all_urls'][0]

        subtitles = {}
        for language in (meta.get('languages') or []):
            subtitles_uri = language.get('subtitles_uri')
            if not (subtitles_uri and language.get('published')):
                continue
            subtitle = subtitles.setdefault(language.get('code') or 'en', [])
            for f in ('json', 'srt', 'vtt'):
                subtitle.append({
                    'ext': f,
                    'url': update_url_query(subtitles_uri, {'format': f}),
                })

        info = {
            'url': video_url,
            'id': video_id,
            'subtitles': subtitles,
            'title': title,
            'description': meta.get('description'),
            'thumbnail': meta.get('thumbnail'),
            'duration': int_or_none(meta.get('duration')),
            'timestamp': parse_iso8601(meta.get('created')),
        }

        for ie in (YoutubeIE, VimeoIE):
            if ie.suitable(video_url):
                info.update({
                    '_type': 'url_transparent',
                    'ie_key': ie.ie_key(),
                })
                break

        return info