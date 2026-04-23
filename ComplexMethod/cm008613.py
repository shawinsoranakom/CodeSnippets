def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        metadata = self._search_json(
            r'window\.__reflectData\s*=', webpage, 'metadata', video_id)

        video_info = metadata['collectionMedia'][0]
        media_data = self._download_json(
            'https://api.gopro.com/media/{}/download'.format(video_info['id']), video_id)

        formats = []
        for fmt in try_get(media_data, lambda x: x['_embedded']['variations']) or []:
            format_url = url_or_none(fmt.get('url'))
            if not format_url:
                continue
            formats.append({
                'url': format_url,
                'format_id': str_or_none(fmt.get('quality')),
                'format_note': str_or_none(fmt.get('label')),
                'ext': str_or_none(fmt.get('type')),
                'width': int_or_none(fmt.get('width')),
                'height': int_or_none(fmt.get('height')),
            })

        title = str_or_none(
            try_get(metadata, lambda x: x['collection']['title'])
            or self._html_search_meta(['og:title', 'twitter:title'], webpage)
            or remove_end(self._html_search_regex(
                r'<title[^>]*>([^<]+)</title>', webpage, 'title', fatal=False), ' | GoPro'))
        if title:
            title = title.replace('\n', ' ')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': url_or_none(
                self._html_search_meta(['og:image', 'twitter:image'], webpage)),
            'timestamp': unified_timestamp(
                try_get(metadata, lambda x: x['collection']['created_at'])),
            'uploader_id': str_or_none(
                try_get(metadata, lambda x: x['account']['nickname'])),
            'duration': int_or_none(
                video_info.get('source_duration')),
            'artist': str_or_none(
                video_info.get('music_track_artist')) or None,
            'track': str_or_none(
                video_info.get('music_track_name')) or None,
        }