def _real_extract(self, url):
        playlist_id = self._match_id(url)

        story = self._download_json(
            'http://api.npr.org/query', playlist_id, query={
                'id': playlist_id,
                'fields': 'audio,multimedia,title',
                'format': 'json',
                'apiKey': 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010',
            })['list']['story'][0]
        playlist_title = story.get('title', {}).get('$text')

        KNOWN_FORMATS = ('threegp', 'm3u8', 'smil', 'mp4', 'mp3')
        quality = qualities(KNOWN_FORMATS)

        entries = []
        for media in story.get('audio', []) + story.get('multimedia', []):
            media_id = media['id']

            formats = []
            for format_id, formats_entry in media.get('format', {}).items():
                if not formats_entry:
                    continue
                if isinstance(formats_entry, list):
                    formats_entry = formats_entry[0]
                format_url = formats_entry.get('$text')
                if not format_url:
                    continue
                if format_id in KNOWN_FORMATS:
                    if format_id == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            format_url, media_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    elif format_id == 'smil':
                        smil_formats = self._extract_smil_formats(
                            format_url, media_id, transform_source=lambda s: s.replace(
                                'rtmp://flash.npr.org/ondemand/', 'https://ondemand.npr.org/'))
                        self._check_formats(smil_formats, media_id)
                        formats.extend(smil_formats)
                    else:
                        formats.append({
                            'url': format_url,
                            'format_id': format_id,
                            'quality': quality(format_id),
                        })
            for stream_id, stream_entry in media.get('stream', {}).items():
                if not isinstance(stream_entry, dict):
                    continue
                if stream_id != 'hlsUrl':
                    continue
                stream_url = url_or_none(stream_entry.get('$text'))
                if not stream_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    stream_url, stream_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            self._sort_formats(formats)

            entries.append({
                'id': media_id,
                'title': media.get('title', {}).get('$text') or playlist_title,
                'thumbnail': media.get('altImageUrl', {}).get('$text'),
                'duration': int_or_none(media.get('duration', {}).get('$text')),
                'formats': formats,
            })

        return self.playlist_result(entries, playlist_id, playlist_title)