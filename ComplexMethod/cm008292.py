def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('path')
        display_id = video_id.lstrip('-')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_regex(
            r'<span[^>]*class="headline"[^>]*>(.+?)</span>',
            webpage, 'title', default=None) or self._og_search_title(webpage, fatal=False)

        entries = []
        videos = re.findall(r'<div[^>]+>', webpage)
        num = 0
        for video in videos:
            video = extract_attributes(video).get('data-config')
            if not video:
                continue
            video = self._parse_json(video, video_id, transform_source=js_to_json, fatal=False)
            video_formats = try_get(video, lambda x: x['mc']['_mediaArray'][0]['_mediaStreamArray'])
            if not video_formats:
                continue
            num += 1
            for video_format in video_formats:
                media_url = video_format.get('_stream') or ''
                formats = []
                if media_url.endswith('master.m3u8'):
                    formats = self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id='hls')
                elif media_url.endswith('.mp3'):
                    formats = [{
                        'url': media_url,
                        'vcodec': 'none',
                    }]
                if not formats:
                    continue
                entries.append({
                    'id': f'{display_id}-{num}',
                    'title': try_get(video, lambda x: x['mc']['_title']),
                    'duration': int_or_none(try_get(video, lambda x: x['mc']['_duration'])),
                    'formats': formats,
                })

        if not entries:
            raise UnsupportedError(url)

        if len(entries) > 1:
            return self.playlist_result(entries, display_id, title)

        return {
            'id': display_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': entries[0]['formats'],
            'timestamp': parse_iso8601(self._html_search_meta('date', webpage)),
            'description': self._og_search_description(webpage),
            'duration': entries[0]['duration'],
        }