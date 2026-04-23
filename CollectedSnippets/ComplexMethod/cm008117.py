def _real_extract(self, url):
        broadcaster_id, broadcast_no = self._match_valid_url(url).group('id', 'bno')
        channel_info = traverse_obj(self._download_json(
            self._LIVE_API_URL, broadcaster_id, data=urlencode_postdata({'bid': broadcaster_id})),
            ('CHANNEL', {dict})) or {}

        broadcaster_id = channel_info.get('BJID') or broadcaster_id
        broadcast_no = channel_info.get('BNO') or broadcast_no
        if not broadcast_no:
            result = channel_info.get('RESULT')
            if result == 0:
                raise UserNotLive(video_id=broadcaster_id)
            elif result == -6:
                self.raise_login_required(
                    'This channel is streaming for subscribers only', method='password')
            raise ExtractorError('Unable to extract broadcast number')

        password = self.get_param('videopassword')
        if channel_info.get('BPWD') == 'Y' and password is None:
            raise ExtractorError(
                'This livestream is protected by a password, use the --video-password option',
                expected=True)

        token_info = traverse_obj(self._download_json(
            self._LIVE_API_URL, broadcast_no, 'Downloading access token for stream',
            'Unable to download access token for stream', data=urlencode_postdata(filter_dict({
                'bno': broadcast_no,
                'stream_type': 'common',
                'type': 'aid',
                'quality': 'master',
                'pwd': password,
            }))), ('CHANNEL', {dict})) or {}
        aid = token_info.get('AID')
        if not aid:
            result = token_info.get('RESULT')
            if result == 0:
                raise ExtractorError('This livestream has ended', expected=True)
            elif result == -6:
                self.raise_login_required('This livestream is for subscribers only', method='password')
            raise ExtractorError('Unable to extract access token')

        formats = self._extract_formats(channel_info, broadcast_no, aid)

        station_info = traverse_obj(self._download_json(
            'https://st.sooplive.com/api/get_station_status.php', broadcast_no,
            'Downloading channel metadata', 'Unable to download channel metadata',
            query={'szBjId': broadcaster_id}, fatal=False), {dict}) or {}

        return {
            'id': broadcast_no,
            'title': channel_info.get('TITLE') or station_info.get('station_title'),
            'uploader': channel_info.get('BJNICK') or station_info.get('station_name'),
            'uploader_id': broadcaster_id,
            'timestamp': parse_iso8601(station_info.get('broad_start'), delimiter=' ', timezone=dt.timedelta(hours=9)),
            'formats': formats,
            'is_live': True,
            'http_headers': {'Referer': url},
        }