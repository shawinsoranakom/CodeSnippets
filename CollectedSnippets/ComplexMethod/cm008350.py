def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(
            url, video_id, headers={'User-Agent': self._USER_AGENT})
        if urlh.url.startswith('https://live.eplus.jp/member/auth'):
            username, password = self._get_login_info()
            if not username:
                self.raise_login_required()
            self._login(username, password, urlh)
            webpage = self._download_webpage(
                url, video_id, headers={'User-Agent': self._USER_AGENT})

        data_json = self._search_json(r'<script>\s*var app\s*=', webpage, 'data json', video_id)

        if data_json.get('drm_mode') == 'ON':
            self.report_drm(video_id)

        if data_json.get('is_pass_ticket') == 'YES':
            raise ExtractorError(
                'This URL is for a pass ticket instead of a player page', expected=True)

        delivery_status = data_json.get('delivery_status')
        archive_mode = data_json.get('archive_mode')
        release_timestamp = try_call(lambda: unified_timestamp(data_json['event_datetime']) - 32400)
        release_timestamp_str = data_json.get('event_datetime_text')  # JST

        self.write_debug(f'delivery_status = {delivery_status}, archive_mode = {archive_mode}')

        if delivery_status == 'PREPARING':
            live_status = 'is_upcoming'
        elif delivery_status == 'STARTED':
            live_status = 'is_live'
        elif delivery_status == 'STOPPED':
            if archive_mode != 'ON':
                raise ExtractorError(
                    'This event has ended and there is no archive for this event', expected=True)
            live_status = 'post_live'
        elif delivery_status == 'WAIT_CONFIRM_ARCHIVED':
            live_status = 'post_live'
        elif delivery_status == 'CONFIRMED_ARCHIVE':
            live_status = 'was_live'
        else:
            self.report_warning(f'Unknown delivery_status {delivery_status}, treat it as a live')
            live_status = 'is_live'

        formats = []

        m3u8_playlist_urls = self._search_json(
            r'var\s+listChannels\s*=', webpage, 'hls URLs', video_id, contains_pattern=r'\[.+\]', default=[])
        if not m3u8_playlist_urls:
            if live_status == 'is_upcoming':
                self.raise_no_formats(
                    f'Could not find the playlist URL. This live event will begin at {release_timestamp_str} JST', expected=True)
            else:
                self.raise_no_formats(
                    'Could not find the playlist URL. This event may not be accessible', expected=True)
        elif live_status == 'is_upcoming':
            self.raise_no_formats(f'This live event will begin at {release_timestamp_str} JST', expected=True)
        elif live_status == 'post_live':
            self.raise_no_formats('This event has ended, and the archive will be available shortly', expected=True)
        else:
            for m3u8_playlist_url in m3u8_playlist_urls:
                formats.extend(self._extract_m3u8_formats(m3u8_playlist_url, video_id))
            # FIXME: HTTP request headers need to be updated to continue download
            warning = 'Due to technical limitations, the download will be interrupted after one hour'
            if live_status == 'is_live':
                self.report_warning(warning)
            elif live_status == 'was_live':
                self.report_warning(f'{warning}. You can restart to continue the download')

        return {
            'id': data_json['app_id'],
            'title': data_json.get('app_name'),
            'formats': formats,
            'live_status': live_status,
            'description': data_json.get('content'),
            'release_timestamp': release_timestamp,
        }