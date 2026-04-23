def _real_extract(self, url):
        video_id = self._match_id(url).replace('_', '/')
        item = self._download_json(
            'http://api-live.dumpert.nl/mobile_api/json/info/' + video_id.replace('/', '_'),
            video_id)['items'][0]
        title = item['title']
        media = next(m for m in item['media'] if m.get('mediatype') == 'VIDEO')

        quality = qualities(['flv', 'mobile', 'tablet', '720p', '1080p'])
        formats = []
        for variant in media.get('variants', []):
            uri = variant.get('uri')
            if not uri:
                continue
            version = variant.get('version')
            preference = quality(version)
            if determine_ext(uri) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    uri, video_id, 'mp4', m3u8_id=version, quality=preference))
            else:
                formats.append({
                    'url': uri,
                    'format_id': version,
                    'quality': preference,
                })

        thumbnails = []
        stills = item.get('stills') or {}
        for t in ('thumb', 'still'):
            for s in ('', '-medium', '-large'):
                still_id = t + s
                still_url = stills.get(still_id)
                if not still_url:
                    continue
                thumbnails.append({
                    'id': still_id,
                    'url': still_url,
                })

        stats = item.get('stats') or {}

        return {
            'id': video_id,
            'title': title,
            'description': item.get('description'),
            'thumbnails': thumbnails,
            'formats': formats,
            'duration': int_or_none(media.get('duration')),
            'like_count': int_or_none(stats.get('kudos_total')),
            'view_count': int_or_none(stats.get('views_total')),
        }