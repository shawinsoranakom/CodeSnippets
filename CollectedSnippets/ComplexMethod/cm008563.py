def _real_extract(self, url):
        content_id = self._match_id(url)
        try:
            data = self._download_json(f'https://10.com.au/api/v1/videos/{content_id}', content_id)
        except ExtractorError as e:
            if (
                isinstance(e.cause, HTTPError) and e.cause.status == 403
                and 'Error 54113' in e.cause.response.read().decode()
            ):
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            raise

        video_data, urlh = self._call_playback_api(content_id)
        content_source_id = video_data['dai']['contentSourceId']
        video_id = video_data['dai']['videoId']
        auth_token = urlh.get_header('x-dai-auth')
        if not auth_token:
            raise ExtractorError('Failed to get DAI auth token')

        dai_data = self._download_json(
            f'https://pubads.g.doubleclick.net/ondemand/hls/content/{content_source_id}/vid/{video_id}/streams',
            content_id, note='Downloading DAI JSON',
            data=urlencode_postdata({'auth-token': auth_token}))

        # Ignore subs to avoid ad break cleanup
        formats, _ = self._extract_m3u8_formats_and_subtitles(
            dai_data['stream_manifest'], content_id, 'mp4')

        already_have_1080p = False
        for fmt in formats:
            m3u8_doc = self._download_webpage(
                fmt['url'], content_id, note='Downloading m3u8 information')
            m3u8_doc = self._filter_ads_from_m3u8(m3u8_doc)
            fmt['hls_media_playlist_data'] = m3u8_doc
            if fmt.get('height') == 1080:
                already_have_1080p = True

        # Attempt format upgrade
        if not already_have_1080p and m3u8_doc and re.search(self._SEGMENT_BITRATE_RE, m3u8_doc):
            m3u8_doc = re.sub(self._SEGMENT_BITRATE_RE, r'-5000000-\1.ts', m3u8_doc)
            m3u8_doc = re.sub(r'-(?:300|150|75|55)0000\.key"', r'-5000000.key"', m3u8_doc)
            formats.append({
                'format_id': 'upgrade-attempt-1080p',
                'url': encode_data_uri(m3u8_doc.encode(), 'application/x-mpegurl'),
                'hls_media_playlist_data': m3u8_doc,
                'width': 1920,
                'height': 1080,
                'ext': 'mp4',
                'protocol': 'm3u8_native',
                '__needs_testing': True,
            })

        return {
            'id': content_id,
            'formats': formats,
            'subtitles': {'en': [{'url': data['captionUrl']}]} if url_or_none(data.get('captionUrl')) else None,
            'uploader': 'Channel 10',
            'uploader_id': '2199827728001',
            **traverse_obj(data, {
                'id': ('altId', {str}),
                'duration': ('duration', {int_or_none}),
                'title': ('subtitle', {str}),
                'alt_title': ('title', {str}),
                'description': ('description', {str}),
                'age_limit': ('classification', {self._AUS_AGES.get}),
                'series': ('tvShow', {str}),
                'season_number': ('season', {int_or_none}),
                'episode_number': ('episode', {int_or_none}),
                'timestamp': ('published', {int_or_none}),
                'thumbnail': ('imageUrl', {url_or_none}),
            }),
        }