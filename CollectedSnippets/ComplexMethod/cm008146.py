def _real_extract(self, url):
        video_id = self._match_id(url)

        channel = self._get_channel(video_id)
        video_id = str(channel['id'])

        is_authorized = next((c for c in self.cookiejar if c.name == 'netviapisessid'), None)
        # cookies starting with "g:" are assigned to guests
        is_authorized = is_authorized is not None and not is_authorized.value.startswith('g:')

        video = self._download_json(
            (self._VIDEO_URL if is_authorized else self._VIDEO_GUEST_URL) % video_id,
            video_id, query={
                'device_type': 'web',
            }, headers=self._HEADERS_WEB,
            expected_status=(200, 422))

        stream_token = try_get(video, lambda x: x['_meta']['error']['info']['stream_token'])
        if stream_token:
            close = self._download_json(
                'https://pilot.wp.pl/api/v1/channels/close', video_id,
                'Invalidating previous stream session', headers=self._HEADERS_WEB,
                data=json.dumps({
                    'channelId': video_id,
                    't': stream_token,
                }).encode())
            if try_get(close, lambda x: x['data']['status']) == 'ok':
                return self.url_result(url, ie=WPPilotIE.ie_key())

        formats = []

        for fmt in video['data']['stream_channel']['streams']:
            # live DASH does not work for now
            # if fmt['type'] == 'dash@live:abr':
            #     formats.extend(
            #         self._extract_mpd_formats(
            #             random.choice(fmt['url']), video_id))
            if fmt['type'] == 'hls@live:abr':
                formats.extend(
                    self._extract_m3u8_formats(
                        random.choice(fmt['url']),
                        video_id, live=True))

        channel['formats'] = formats
        return channel