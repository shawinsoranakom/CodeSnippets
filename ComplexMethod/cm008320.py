def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, video_id, expected_status=404)
        if err_msg := traverse_obj(webpage, ({find_element(cls='message')}, {clean_html})):
            raise ExtractorError(err_msg, expected=True)

        age_limit = 18 if 'age_auth' in urlh.url else None
        if age_limit:
            if not self.is_logged_in:
                self.raise_login_required('Login is required to access age-restricted content')

            my = self._download_webpage('https://www.nicovideo.jp/my', None, 'Checking age verification')
            if traverse_obj(my, (
                {find_element(id='js-initial-userpage-data', html=True)}, {extract_attributes},
                'data-environment', {json.loads}, 'allowSensitiveContents', {bool},
            )):
                self._set_cookie('.nicovideo.jp', 'age_auth', '1')
                webpage = self._download_webpage(url, video_id)
            else:
                raise ExtractorError('Sensitive content setting must be enabled', expected=True)

        embedded_data = traverse_obj(webpage, (
            {find_element(tag='script', id='embedded-data', html=True)},
            {extract_attributes}, 'data-props', {json.loads}))
        frontend_id = traverse_obj(embedded_data, ('site', 'frontendId', {str_or_none}), default='9')

        ws_url = traverse_obj(embedded_data, (
            'site', 'relive', 'webSocketUrl', {url_or_none}, {require('websocket URL')}))
        ws_url = update_url_query(ws_url, {'frontend_id': frontend_id})
        ws = self._request_webpage(
            ws_url, video_id, 'Connecting to WebSocket server',
            headers={'Origin': 'https://live.nicovideo.jp'})

        self.write_debug('Sending HLS server request')
        ws.send(json.dumps({
            'data': {
                'reconnect': False,
                'room': {
                    'commentable': True,
                    'protocol': 'webSocket',
                },
                'stream': {
                    'accessRightMethod': 'single_cookie',
                    'chasePlay': False,
                    'latency': 'high',
                    'protocol': 'hls',
                    'quality': 'abr',
                },
            },
            'type': 'startWatching',
        }))

        while True:
            recv = ws.recv()
            if not recv:
                continue
            data = json.loads(recv)
            if not isinstance(data, dict):
                continue
            if data.get('type') == 'stream':
                m3u8_url = data['data']['uri']
                qualities = data['data']['availableQualities']
                cookies = data['data']['cookies']
                break
            elif data.get('type') == 'disconnect':
                self.write_debug(recv)
                raise ExtractorError('Disconnected at middle of extraction')
            elif data.get('type') == 'error':
                self.write_debug(recv)
                message = traverse_obj(data, ('body', 'code', {str_or_none}), default=recv)
                raise ExtractorError(message)
            elif self.get_param('verbose', False):
                self.write_debug(f'Server response: {truncate_string(recv, 100)}')

        title = traverse_obj(embedded_data, ('program', 'title')) or self._html_search_meta(
            ('og:title', 'twitter:title'), webpage, 'live title', fatal=False)

        raw_thumbs = traverse_obj(embedded_data, ('program', 'thumbnail', {dict})) or {}
        thumbnails = []
        for name, value in raw_thumbs.items():
            if not isinstance(value, dict):
                thumbnails.append({
                    'id': name,
                    'url': value,
                    **parse_resolution(value, lenient=True),
                })
                continue

            for k, img_url in value.items():
                res = parse_resolution(k, lenient=True) or parse_resolution(img_url, lenient=True)
                width, height = res.get('width'), res.get('height')

                thumbnails.append({
                    'id': f'{name}_{width}x{height}',
                    'url': img_url,
                    'ext': traverse_obj(parse_qs(img_url), ('image', 0, {determine_ext(default_ext='jpg')})),
                    **res,
                })

        for cookie in cookies:
            self._set_cookie(
                cookie['domain'], cookie['name'], cookie['value'],
                expire_time=unified_timestamp(cookie.get('expires')), path=cookie['path'], secure=cookie['secure'])

        q_iter = (q for q in qualities[1:] if not q.startswith('audio_'))  # ignore initial 'abr'
        a_map = {96: 'audio_low', 192: 'audio_high'}

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4', live=True)
        for fmt in formats:
            fmt['protocol'] = 'niconico_live'
            if fmt.get('acodec') == 'none':
                fmt['format_id'] = next(q_iter, fmt['format_id'])
            elif fmt.get('vcodec') == 'none':
                abr = parse_bitrate(fmt['url'].lower())
                fmt.update({
                    'abr': abr,
                    'acodec': 'mp4a.40.2',
                    'format_id': a_map.get(abr, fmt['format_id']),
                })

        return {
            'id': video_id,
            'title': title,
            'age_limit': age_limit,
            'downloader_options': {
                'max_quality': traverse_obj(embedded_data, ('program', 'stream', 'maxQuality', {str})) or 'normal',
                'ws': ws,
                'ws_url': ws_url,
            },
            **traverse_obj(embedded_data, {
                'view_count': ('program', 'statistics', 'watchCount'),
                'comment_count': ('program', 'statistics', 'commentCount'),
                'uploader': ('program', 'supplier', 'name'),
                'channel': ('socialGroup', 'name'),
                'channel_id': ('socialGroup', 'id'),
                'channel_url': ('socialGroup', 'socialGroupPageUrl'),
            }),
            'description': clean_html(traverse_obj(embedded_data, ('program', 'description'))),
            'timestamp': int_or_none(traverse_obj(embedded_data, ('program', 'openTime'))),
            'is_live': True,
            'thumbnails': thumbnails,
            'formats': formats,
        }