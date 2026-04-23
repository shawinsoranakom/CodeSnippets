def _real_extract(self, url):
        base_url, url_type, video_id = self._match_valid_url(url).group('base_url', 'type', 'id')
        query = {}
        start_params = traverse_obj(url, {'startTime': ({parse_qs}, 'startTime', -1)})

        if url_type == 'share':
            webpage = self._get_real_webpage(url, base_url, video_id, 'share')
            meeting_id = self._get_page_data(webpage, video_id)['meetingId']
            redirect_path = self._download_json(
                f'{base_url}nws/recording/1.0/play/share-info/{meeting_id}',
                video_id, note='Downloading share info JSON')['result']['redirectUrl']
            url = update_url_query(urljoin(base_url, redirect_path), start_params)
            query['continueMode'] = 'true'

        webpage = self._get_real_webpage(url, base_url, video_id, 'play')
        file_id = self._get_page_data(webpage, video_id)['fileId']
        if not file_id:
            # When things go wrong, file_id can be empty string
            raise ExtractorError('Unable to extract file ID')

        query.update(start_params)
        data = self._download_json(
            f'{base_url}nws/recording/1.0/play/info/{file_id}', video_id, query=query,
            note='Downloading play info JSON')['result']

        subtitles = {}
        for _type in ('transcript', 'cc', 'chapter'):
            if data.get(f'{_type}Url'):
                subtitles[_type] = [{
                    'url': urljoin(base_url, data[f'{_type}Url']),
                    'ext': 'vtt',
                }]

        formats = []

        if data.get('viewMp4Url'):
            formats.append({
                'format_note': 'Camera stream',
                'url': data['viewMp4Url'],
                'width': int_or_none(traverse_obj(data, ('viewResolvtions', 0))),
                'height': int_or_none(traverse_obj(data, ('viewResolvtions', 1))),
                'format_id': 'view',
                'ext': 'mp4',
                'filesize_approx': parse_filesize(str_or_none(traverse_obj(data, ('recording', 'fileSizeInMB')))),
                'preference': 0,
            })

        if data.get('shareMp4Url'):
            formats.append({
                'format_note': 'Screen share stream',
                'url': data['shareMp4Url'],
                'width': int_or_none(traverse_obj(data, ('shareResolvtions', 0))),
                'height': int_or_none(traverse_obj(data, ('shareResolvtions', 1))),
                'format_id': 'share',
                'ext': 'mp4',
                'preference': -1,
            })

        view_with_share_url = data.get('viewMp4WithshareUrl')
        if view_with_share_url:
            formats.append({
                **parse_resolution(self._search_regex(
                    r'_(\d+x\d+)\.mp4', url_basename(view_with_share_url), 'resolution', default=None)),
                'format_note': 'Screen share with camera',
                'url': view_with_share_url,
                'format_id': 'view_with_share',
                'ext': 'mp4',
                'preference': 1,
            })

        return {
            'id': video_id,
            'title': str_or_none(traverse_obj(data, ('meet', 'topic'))),
            'duration': int_or_none(data.get('duration')),
            'subtitles': subtitles,
            'formats': formats,
            'http_headers': {
                'Referer': base_url,
            },
        }