def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, headers=traverse_obj(smuggled_data, {'Referer': 'referer'}))
        data = self._search_json(
            r'(?:window\.|(?:var|const|let)\s+)(?:dat|(?:player|video)Info|)\s*=\s*["\']', webpage,
            'player info', video_id, contains_pattern=r'[A-Za-z0-9+/=]+', end_pattern=r'["\'];',
            transform_source=lambda x: base64.b64decode(x).decode())

        # SproutVideo may send player info for 'SMPTE Color Monitor Test' [a791d7b71b12ecc52e]
        # e.g. if the user-agent we used with the webpage request is too old
        video_uid = data['videoUid']
        if video_id != video_uid:
            raise ExtractorError(f'{self.IE_NAME} sent the wrong video data ({video_uid})')

        formats, subtitles = [], {}
        headers = {
            'Accept': '*/*',
            'Origin': 'https://videos.sproutvideo.com',
            'Referer': url,
        }

        # HLS extraction is fatal; only attempt it if the JSON data says it's available
        if traverse_obj(data, 'hls'):
            manifest_query = self._policy_to_qs(data, 'm')
            fragment_query = self._policy_to_qs(data, 't', as_string=True)
            key_query = self._policy_to_qs(data, 'k', as_string=True)

            formats.extend(self._extract_m3u8_formats(
                self._M3U8_URL_TMPL.format(**data), video_id, 'mp4',
                m3u8_id='hls', headers=headers, query=manifest_query))
            for fmt in formats:
                fmt.update({
                    'url': update_url_query(fmt['url'], manifest_query),
                    'extra_param_to_segment_url': fragment_query,
                    'extra_param_to_key_url': key_query,
                })

        if downloads := traverse_obj(data, ('downloads', {dict.items}, lambda _, v: url_or_none(v[1]))):
            quality = qualities(self._QUALITIES)
            acodec = 'none' if data.get('has_audio') is False else None
            formats.extend([{
                'format_id': str(format_id),
                'url': format_url,
                'ext': 'mp4',
                'quality': quality(format_id),
                'acodec': acodec,
            } for format_id, format_url in downloads])

        for sub_data in traverse_obj(data, ('subtitleData', lambda _, v: url_or_none(v['src']))):
            subtitles.setdefault(sub_data.get('srclang', 'en'), []).append({
                'url': sub_data['src'],
            })

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
            **traverse_obj(data, {
                'title': ('title', {str}),
                'duration': ('duration', {int_or_none}),
                'thumbnail': ('posterframe_url', {url_or_none}),
            }),
        }