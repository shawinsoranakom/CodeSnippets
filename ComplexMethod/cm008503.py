def _real_extract(self, url):
        video_type, video_id = self._match_valid_url(url).group('type', 'id')
        live_from_start = self.get_param('live_from_start')

        if video_type == 'live':
            project_id = 'tver-olympic-live'
            api_key = 'a35ebb1ca7d443758dc7fcc5d99b1f72'
            olympic_data = traverse_obj(self._download_json(
                f'{self._API_BASE}/live/{video_id}', video_id), ('contents', 'live', {dict}))
            media_id = traverse_obj(olympic_data, ('video_id', {str}))

            now = time_seconds()
            start_timestamp_str = traverse_obj(olympic_data, ('onair_start_date', {str}))
            start_timestamp = unified_timestamp(start_timestamp_str, tz_offset=9)
            if not start_timestamp:
                raise ExtractorError('Unable to extract on-air start time')
            end_timestamp = traverse_obj(olympic_data, (
                'onair_end_date', {unified_timestamp(tz_offset=9)}, {require('on-air end time')}))

            if now < start_timestamp:
                self.raise_no_formats(
                    f'This program is scheduled to start at {start_timestamp_str} JST', expected=True)

                return {
                    'id': video_id,
                    'live_status': 'is_upcoming',
                    'release_timestamp': start_timestamp,
                }
            elif start_timestamp <= now < end_timestamp:
                live_status = 'is_live'
                if live_from_start:
                    media_id += '_dvr'
            elif end_timestamp <= now:
                dvr_end_timestamp = traverse_obj(olympic_data, (
                    'dvr_end_date', {unified_timestamp(tz_offset=9)}))
                if dvr_end_timestamp and now < dvr_end_timestamp:
                    live_status = 'was_live'
                    media_id += '_dvr'
                else:
                    raise ExtractorError(
                        'This program is no longer available', expected=True)
        else:
            project_id = 'tver-olympic'
            api_key = '4b55a4db3cce4ad38df6dd8543e3e46a'
            media_id = video_id
            live_status = 'not_live'
            olympic_data = traverse_obj(self._download_json(
                f'{self._API_BASE}/video/{video_id}', video_id), ('contents', 'video', {dict}))

        return {
            **self._extract_from_streaks_api(project_id, f'ref:{media_id}', {
                'Origin': 'https://tver.jp',
                'Referer': 'https://tver.jp/',
                'X-Streaks-Api-Key': api_key,
            }, live_from_start=live_from_start),
            **traverse_obj(olympic_data, {
                'title': ('title', {clean_html}, filter),
                'alt_title': ('sub_title', {clean_html}, filter),
                'channel': ('channel', {clean_html}, filter),
                'channel_id': ('channel_id', {clean_html}, filter),
                'description': (('description', 'description_l', 'description_s'), {clean_html}, filter, any),
                'timestamp': ('onair_start_date', {unified_timestamp(tz_offset=9)}),
                'thumbnail': (('picture_l_url', 'picture_m_url', 'picture_s_url'), {url_or_none}, any),
            }),
            'id': video_id,
            'live_status': live_status,
        }