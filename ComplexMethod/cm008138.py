def _real_extract(self, url):
        uploader_id, video_id = self._match_valid_url(url).groups()

        webpage, urlh = self._download_webpage_handle(url, video_id)
        video_password = self.get_param('videopassword')
        request_data = None
        if video_password:
            request_data = urlencode_postdata({
                'password': video_password,
                **self._hidden_inputs(webpage),
            }, encoding='utf-8')
            webpage, urlh = self._download_webpage_handle(
                url, video_id, data=request_data,
                headers={'Origin': 'https://twitcasting.tv'},
                note='Trying video password')
        if urlh.url != url and request_data:
            webpage = self._download_webpage(
                urlh.url, video_id, data=request_data,
                headers={'Origin': 'https://twitcasting.tv'},
                note='Retrying authentication')
        # has to check here as the first request can contain password input form even if the password is correct
        if re.search(r'<form\s+method="POST">\s*<input\s+[^>]+?name="password"', webpage):
            raise ExtractorError('This video is protected by a password, use the --video-password option', expected=True)

        title = (clean_html(get_element_by_id('movietitle', webpage))
                 or self._html_search_meta(['og:title', 'twitter:title'], webpage, fatal=True))

        video_js_data = try_get(
            webpage,
            lambda x: self._parse_data_movie_playlist(self._search_regex(
                r'data-movie-playlist=\'([^\']+?)\'',
                x, 'movie playlist', default=None), video_id)['2'], list)

        thumbnail = traverse_obj(video_js_data, (0, 'thumbnailUrl')) or self._og_search_thumbnail(webpage)
        description = clean_html(get_element_by_id(
            'authorcomment', webpage)) or self._html_search_meta(
            ['description', 'og:description', 'twitter:description'], webpage)
        duration = (try_get(video_js_data, lambda x: sum(float_or_none(y.get('duration')) for y in x) / 1000)
                    or parse_duration(clean_html(get_element_by_class('tw-player-duration-time', webpage))))
        view_count = str_to_int(self._search_regex(
            (r'Total\s*:\s*Views\s*([\d,]+)', r'総視聴者\s*:\s*([\d,]+)\s*</'), webpage, 'views', None))
        timestamp = unified_timestamp(self._search_regex(
            r'data-toggle="true"[^>]+datetime="([^"]+)"',
            webpage, 'datetime', None))

        is_live = any(f'data-{x}' in webpage for x in ['is-onlive="true"', 'live-type="live"', 'status="online"'])

        base_dict = {
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'is_live': is_live,
        }

        def find_dmu(x):
            data_movie_url = self._search_regex(
                r'data-movie-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
                x, 'm3u8 url', group='url', default=None)
            if data_movie_url:
                return [data_movie_url]

        m3u8_urls = (try_get(webpage, find_dmu, list)
                     or traverse_obj(video_js_data, (..., 'source', 'url')))

        if is_live:
            stream_data = self._download_json(
                'https://twitcasting.tv/streamserver.php',
                video_id, 'Downloading live info', query={
                    'target': uploader_id,
                    'mode': 'client',
                    'player': 'pc_web',
                })

            password_params = {
                'word': hashlib.md5(video_password.encode()).hexdigest(),
            } if video_password else None

            formats = []
            # low: 640x360, medium: 1280x720, high: 1920x1080
            qq = qualities(['low', 'medium', 'high'])
            for quality, m3u8_url in traverse_obj(stream_data, (
                'tc-hls', 'streams', {dict.items}, lambda _, v: url_or_none(v[1]),
            )):
                formats.append({
                    'url': update_url_query(m3u8_url, password_params),
                    'format_id': f'hls-{quality}',
                    'ext': 'mp4',
                    'quality': qq(quality),
                    'protocol': 'm3u8',
                    'http_headers': self._M3U8_HEADERS,
                })

            if websockets:
                qq = qualities(['base', 'mobilesource', 'main'])
                for mode, ws_url in traverse_obj(stream_data, (
                    'llfmp4', 'streams', {dict.items}, lambda _, v: url_or_none(v[1]),
                )):
                    formats.append({
                        'url': update_url_query(ws_url, password_params),
                        'format_id': f'ws-{mode}',
                        'ext': 'mp4',
                        'quality': qq(mode),
                        'source_preference': -10,
                        # TwitCasting simply sends moof atom directly over WS
                        'protocol': 'websocket_frag',
                    })

            if not formats:
                self.raise_login_required()

            infodict = {
                'formats': formats,
                '_format_sort_fields': ('source', ),
            }
        elif not m3u8_urls:
            raise ExtractorError('Failed to get m3u8 playlist')
        elif len(m3u8_urls) == 1:
            formats = self._extract_m3u8_formats(
                m3u8_urls[0], video_id, 'mp4', headers=self._M3U8_HEADERS)
            infodict = {
                # No problem here since there's only one manifest
                'formats': formats,
                'http_headers': self._M3U8_HEADERS,
            }
        else:
            infodict = {
                '_type': 'multi_video',
                'entries': [{
                    'id': f'{video_id}-{num}',
                    'url': m3u8_url,
                    'ext': 'mp4',
                    # Requesting the manifests here will cause download to fail.
                    # So use ffmpeg instead. See: https://github.com/yt-dlp/yt-dlp/issues/382
                    'protocol': 'm3u8',
                    'http_headers': self._M3U8_HEADERS,
                    **base_dict,
                } for (num, m3u8_url) in enumerate(m3u8_urls)],
            }

        return {
            'id': video_id,
            **base_dict,
            **infodict,
        }