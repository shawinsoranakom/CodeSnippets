def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_api(
            'station/video/a/view', video_id, headers={'Referer': url},
            data=urlencode_postdata({
                'nTitleNo': video_id,
                'nApiLevel': 10,
            }))['data']

        initial_refresh_time = 0
        strm_id = None
        # For subscriber-only VODs, we need to call private_auth.php to get CloudFront cookies
        needs_private_auth = traverse_obj(data, ('sub_upload_type', {str}))
        if needs_private_auth:
            strm_id = traverse_obj(data, ('bj_id', {str}, {require('stream ID')}))

        error_code = traverse_obj(data, ('code', {int}))
        if error_code == -6221:
            raise ExtractorError('The VOD does not exist', expected=True)
        elif error_code == -6205:
            raise ExtractorError('This VOD is private', expected=True)

        common_info = traverse_obj(data, {
            'title': ('title', {str}),
            'uploader': ('writer_nick', {str}),
            'uploader_id': ('bj_id', {str}),
            'duration': ('total_file_duration', {int_or_none(scale=1000)}),
            'thumbnails': ('thumb', {self._fixup_thumb}),
        })

        entries = []
        for file_num, file_element in enumerate(
                traverse_obj(data, ('files', lambda _, v: url_or_none(v['file']))), start=1):
            file_url = file_element['file']
            if determine_ext(file_url) == 'm3u8':
                if needs_private_auth:
                    self._request_webpage(
                        _cloudfront_auth_request(file_url, strm_id, video_id, url),
                        video_id, 'Requesting CloudFront cookies', 'Failed to get CloudFront cookies')
                    initial_refresh_time = time.time()
                formats = self._extract_m3u8_formats(
                    file_url, video_id, 'mp4', m3u8_id='hls',
                    note=f'Downloading part {file_num} m3u8 information')
                if needs_private_auth:
                    for fmt in formats:
                        fmt['protocol'] = 'soopvod'
                        fmt['_cookie_refresh_params'] = {
                            'm3u8_url': file_url,
                            'strm_id': strm_id,
                            'video_id': video_id,
                            '_last_refresh': initial_refresh_time,
                        }
            else:
                formats = [{
                    'url': file_url,
                    'format_id': 'http',
                }]

            entries.append({
                **common_info,
                'id': file_element.get('file_info_key') or f'{video_id}_{file_num}',
                'title': f'{common_info.get("title") or "Untitled"} (part {file_num})',
                'formats': formats,
                **traverse_obj(file_element, {
                    'duration': ('duration', {int_or_none(scale=1000)}),
                    'timestamp': ('file_start', {parse_iso8601(delimiter=' ', timezone=dt.timedelta(hours=9))}),
                }),
            })

        if traverse_obj(data, ('adult_status', {str})) == 'notLogin':
            if not entries:
                self.raise_login_required(
                    'Only users older than 19 are able to watch this video', method='password')
            self.report_warning(
                'In accordance with local laws and regulations, underage users are '
                'restricted from watching adult content. Only content suitable for all '
                f'ages will be downloaded. {self._login_hint("password")}')

        if not entries and traverse_obj(data, ('sub_upload_type', {str})):
            self.raise_login_required('This VOD is for subscribers only', method='password')

        if len(entries) == 1:
            return {
                **entries[0],
                'title': common_info.get('title'),
            }

        common_info['timestamp'] = traverse_obj(entries, (..., 'timestamp'), get_all=False)

        return self.playlist_result(entries, video_id, multi_video=True, **common_info)