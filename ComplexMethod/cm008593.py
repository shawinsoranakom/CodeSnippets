def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id=video_id)
        stream_data = self._search_json(r'stream:\s', webpage, 'stream', video_id=video_id, default=None)
        room_info = try_get(stream_data, lambda x: x['data'][0]['gameLiveInfo'])
        if not room_info:
            raise ExtractorError('Can not extract the room info', expected=True)
        title = room_info.get('roomName') or room_info.get('introduction') or self._html_extract_title(webpage)
        screen_type = room_info.get('screenType')
        live_source_type = room_info.get('liveSourceType')
        stream_info_list = stream_data['data'][0]['gameStreamInfoList']
        if not stream_info_list:
            raise ExtractorError('Video is offline', expected=True)
        formats = []
        for stream_info in stream_info_list:
            stream_url = stream_info.get('sFlvUrl')
            if not stream_url:
                continue
            stream_name = stream_info.get('sStreamName')
            re_secret = not screen_type and live_source_type in (0, 8, 13)
            params = dict(urllib.parse.parse_qsl(unescapeHTML(stream_info['sFlvAntiCode'])))
            fm, ss = '', ''
            if re_secret:
                fm, ss = self.encrypt(params, stream_info, stream_name)
            for si in stream_data.get('vMultiStreamInfo'):
                display_name, bitrate = re.fullmatch(
                    r'(.+?)(?:(\d+)M)?', si.get('sDisplayName')).groups()
                rate = si.get('iBitRate')
                if rate:
                    params['ratio'] = rate
                else:
                    params.pop('ratio', None)
                    if bitrate:
                        rate = int(bitrate) * 1000
                if re_secret:
                    params['wsSecret'] = hashlib.md5(
                        '_'.join([fm, params['u'], stream_name, ss, params['wsTime']]))
                formats.append({
                    'ext': stream_info.get('sFlvUrlSuffix'),
                    'format_id': str_or_none(stream_info.get('iLineIndex')),
                    'tbr': rate,
                    'url': update_url_query(f'{stream_url}/{stream_name}.{stream_info.get("sFlvUrlSuffix")}',
                                            query=params),
                    **self._RESOLUTION.get(display_name, {}),
                })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'view_count': room_info.get('totalCount'),
            'thumbnail': room_info.get('screenshot'),
            'description': room_info.get('contentIntro'),
            'http_headers': {
                'Origin': 'https://www.huya.com',
                'Referer': 'https://www.huya.com/',
            },
        }