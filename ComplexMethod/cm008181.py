def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        video_id, library_id = self._match_valid_url(url).group('id', 'library_id')
        webpage = self._download_webpage(
            f'https://iframe.mediadelivery.net/embed/{library_id}/{video_id}', video_id,
            headers={'Referer': smuggled_data.get('Referer') or 'https://iframe.mediadelivery.net/'},
            query=traverse_obj(parse_qs(url), {'token': 'token', 'expires': 'expires'}))

        if html_title := self._html_extract_title(webpage, default=None) == '403':
            raise ExtractorError(
                'This video is inaccessible. Setting a Referer header '
                'might be required to access the video', expected=True)
        elif html_title == '404':
            raise ExtractorError('This video does not exist', expected=True)

        headers = {'Referer': url}

        info = traverse_obj(self._parse_html5_media_entries(url, webpage, video_id, _headers=headers), 0) or {}
        formats = info.get('formats') or []
        subtitles = info.get('subtitles') or {}

        original_url = self._search_regex(
            r'(?:var|const|let)\s+originalUrl\s*=\s*["\']([^"\']+)["\']', webpage, 'original url', default=None)
        if url_or_none(original_url):
            urlh = self._request_webpage(
                HEADRequest(original_url), video_id=video_id, note='Checking original',
                headers=headers, fatal=False, expected_status=(403, 404))
            if urlh and urlh.status == 200:
                formats.append({
                    'url': original_url,
                    'format_id': 'source',
                    'quality': 1,
                    'http_headers': headers,
                    'ext': urlhandle_detect_ext(urlh, default='mp4'),
                    'filesize': int_or_none(urlh.get_header('Content-Length')),
                })

        # MediaCage Streams require activation and pings
        src_url = self._search_regex(
            r'\.setAttribute\([\'"]src[\'"],\s*[\'"]([^\'"]+)[\'"]\)', webpage, 'src url', default=None)
        activation_url = self._search_regex(
            r'loadUrl\([\'"]([^\'"]+/activate)[\'"]', webpage, 'activation url', default=None)
        ping_url = self._search_regex(
            r'loadUrl\([\'"]([^\'"]+/ping)[\'"]', webpage, 'ping url', default=None)
        secret = traverse_obj(parse_qs(src_url), ('secret', 0))
        context_id = traverse_obj(parse_qs(src_url), ('contextId', 0))
        ping_data = {}
        if src_url and activation_url and ping_url and secret and context_id:
            self._download_webpage(
                activation_url, video_id, headers=headers, note='Downloading activation data')

            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                src_url, video_id, 'mp4', headers=headers, m3u8_id='hls', fatal=False)
            for fmt in fmts:
                fmt.update({
                    'protocol': 'bunnycdn',
                    'http_headers': headers,
                })
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

            ping_data = {
                '_bunnycdn_ping_data': {
                    'url': ping_url,
                    'headers': headers,
                    'secret': secret,
                    'context_id': context_id,
                },
            }

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(webpage, ({find_element(id='main-video', html=True)}, {extract_attributes}, {
                'title': ('data-plyr-config', {json.loads}, 'title', {str}),
                'thumbnail': ('data-poster', {url_or_none}),
            })),
            **ping_data,
            **self._search_json_ld(webpage, video_id, fatal=False),
        }