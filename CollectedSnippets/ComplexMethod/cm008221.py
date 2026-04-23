def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://live.fc2.com/{video_id}/', video_id)

        self._set_cookie('live.fc2.com', 'js-player_size', '1')

        member_api = self._download_json(
            'https://live.fc2.com/api/memberApi.php', video_id, data=urlencode_postdata({
                'channel': '1',
                'profile': '1',
                'user': '1',
                'streamid': video_id,
            }), note='Requesting member info')

        control_server = self._download_json(
            'https://live.fc2.com/api/getControlServer.php', video_id, note='Downloading ControlServer data',
            data=urlencode_postdata({
                'channel_id': video_id,
                'mode': 'play',
                'orz': '',
                'channel_version': member_api['data']['channel_data']['version'],
                'client_version': '2.1.0\n [1]',
                'client_type': 'pc',
                'client_app': 'browser_hls',
                'ipv6': '',
            }), headers={'X-Requested-With': 'XMLHttpRequest'})
        # A non-zero 'status' indicates the stream is not live, so check truthiness
        if traverse_obj(control_server, ('status', {int})) and 'control_token' not in control_server:
            raise UserNotLive(video_id=video_id)
        self._set_cookie('live.fc2.com', 'l_ortkn', control_server['orz_raw'])

        ws_url = update_url_query(control_server['url'], {'control_token': control_server['control_token']})
        playlist_data = None

        ws = self._request_webpage(Request(ws_url, headers={
            'Origin': 'https://live.fc2.com',
        }), video_id, note='Fetching HLS playlist info via WebSocket')

        self.write_debug('Sending HLS server request')

        while True:
            recv = ws.recv()
            if not recv:
                continue
            data = self._parse_json(recv, video_id, fatal=False)
            if not data or not isinstance(data, dict):
                continue

            if data.get('name') == 'connect_complete':
                break
        ws.send(r'{"name":"get_hls_information","arguments":{},"id":1}')

        while True:
            recv = ws.recv()
            if not recv:
                continue
            data = self._parse_json(recv, video_id, fatal=False)
            if not data or not isinstance(data, dict):
                continue
            if data.get('name') == '_response_' and data.get('id') == 1:
                self.write_debug('Goodbye')
                playlist_data = data
                break
            self.write_debug('Server said: {}{}'.format(recv[:100], '...' if len(recv) > 100 else ''))

        if not playlist_data:
            raise ExtractorError('Unable to fetch HLS playlist info via WebSocket')

        formats = []
        for name, playlists in playlist_data['arguments'].items():
            if not isinstance(playlists, list):
                continue
            for pl in playlists:
                if pl.get('status') == 0 and 'master_playlist' in pl.get('url'):
                    formats.extend(self._extract_m3u8_formats(
                        pl['url'], video_id, ext='mp4', m3u8_id=name, live=True,
                        headers={
                            'Origin': 'https://live.fc2.com',
                            'Referer': url,
                        }))

        for fmt in formats:
            fmt.update({
                'protocol': 'fc2_live',
                'ws': ws,
            })

        title = self._html_search_meta(('og:title', 'twitter:title'), webpage, 'live title', fatal=False)
        if not title:
            title = self._html_extract_title(webpage, 'html title', fatal=False)
            if title:
                # remove service name in <title>
                title = re.sub(r'\s+-\s+.+$', '', title)
        uploader = None
        if title:
            match = self._search_regex(r'^(.+?)\s*\[(.+?)\]$', title, 'title and uploader', default=None, group=(1, 2))
            if match and all(match):
                title, uploader = match

        live_info_view = self._search_regex(r'(?s)liveInfoView\s*:\s*({.+?}),\s*premiumStateView', webpage, 'user info', fatal=False) or None
        if live_info_view:
            # remove jQuery code from object literal
            live_info_view = re.sub(r'\$\(.+?\)[^,]+,', '"",', live_info_view)
            live_info_view = self._parse_json(js_to_json(live_info_view), video_id)

        return {
            'id': video_id,
            'title': title or traverse_obj(live_info_view, 'title'),
            'description': self._html_search_meta(
                ('og:description', 'twitter:description'),
                webpage, 'live description', fatal=False) or traverse_obj(live_info_view, 'info'),
            'formats': formats,
            'uploader': uploader or traverse_obj(live_info_view, 'name'),
            'uploader_id': video_id,
            'thumbnail': traverse_obj(live_info_view, 'thumb'),
            'is_live': True,
        }