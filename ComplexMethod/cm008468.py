def _real_extract(self, url):
        uploader, room_id = self._match_valid_url(url).group('uploader', 'id')
        if not room_id:
            webpage = self._download_webpage(
                format_field(uploader, None, self._UPLOADER_URL_FORMAT), uploader, impersonate=True)
            room_id = traverse_obj(
                self._get_universal_data(webpage, uploader),
                ('webapp.user-detail', 'userInfo', 'user', 'roomId', {str}))

        if not uploader or not room_id:
            webpage = self._download_webpage(url, uploader or room_id, fatal=not room_id)
            data = self._get_sigi_state(webpage, uploader or room_id)
            room_id = room_id or traverse_obj(data, ((
                ('LiveRoom', 'liveRoomUserInfo', 'user'),
                ('UserModule', 'users', ...)), 'roomId', {str}, any))
            uploader = uploader or traverse_obj(data, ((
                ('LiveRoom', 'liveRoomUserInfo', 'user'),
                ('UserModule', 'users', ...)), 'uniqueId', {str}, any))

        if not room_id:
            raise UserNotLive(video_id=uploader)

        formats = []
        live_info = self._call_api(
            'https://webcast.tiktok.com/webcast/room/info', 'room_id', room_id, uploader, key='data')

        get_quality = qualities(('SD1', 'ld', 'SD2', 'sd', 'HD1', 'hd', 'FULL_HD1', 'uhd', 'ORIGION', 'origin'))
        parse_inner = lambda x: self._parse_json(x, None)

        for quality, stream in traverse_obj(live_info, (
                'stream_url', 'live_core_sdk_data', 'pull_data', 'stream_data',
                {parse_inner}, 'data', {dict}), default={}).items():

            sdk_params = traverse_obj(stream, ('main', 'sdk_params', {parse_inner}, {
                'vcodec': ('VCodec', {str}),
                'tbr': ('vbitrate', {int_or_none(scale=1000)}),
                'resolution': ('resolution', {lambda x: re.match(r'(?i)\d+x\d+|\d+p', x).group().lower()}),
            }))

            flv_url = traverse_obj(stream, ('main', 'flv', {url_or_none}))
            if flv_url:
                formats.append({
                    'url': flv_url,
                    'ext': 'flv',
                    'format_id': f'flv-{quality}',
                    'quality': get_quality(quality),
                    **sdk_params,
                })

            hls_url = traverse_obj(stream, ('main', 'hls', {url_or_none}))
            if hls_url:
                formats.append({
                    'url': hls_url,
                    'ext': 'mp4',
                    'protocol': 'm3u8_native',
                    'format_id': f'hls-{quality}',
                    'quality': get_quality(quality),
                    **sdk_params,
                })

        def get_vcodec(*keys):
            return traverse_obj(live_info, (
                'stream_url', *keys, {parse_inner}, 'VCodec', {str}))

        for stream in ('hls', 'rtmp'):
            stream_url = traverse_obj(live_info, ('stream_url', f'{stream}_pull_url', {url_or_none}))
            if stream_url:
                formats.append({
                    'url': stream_url,
                    'ext': 'mp4' if stream == 'hls' else 'flv',
                    'protocol': 'm3u8_native' if stream == 'hls' else 'https',
                    'format_id': f'{stream}-pull',
                    'vcodec': get_vcodec(f'{stream}_pull_url_params'),
                    'quality': get_quality('ORIGION'),
                })

        for f_id, f_url in traverse_obj(live_info, ('stream_url', 'flv_pull_url', {dict}), default={}).items():
            if not url_or_none(f_url):
                continue
            formats.append({
                'url': f_url,
                'ext': 'flv',
                'format_id': f'flv-{f_id}'.lower(),
                'vcodec': get_vcodec('flv_pull_url_params', f_id),
                'quality': get_quality(f_id),
            })

        # If uploader is a guest on another's livestream, primary endpoint will not have m3u8 URLs
        if not traverse_obj(formats, lambda _, v: v['ext'] == 'mp4'):
            live_info = merge_dicts(live_info, self._call_api(
                'https://www.tiktok.com/api/live/detail/', 'roomID', room_id, uploader, key='LiveRoomInfo'))
            if url_or_none(live_info.get('liveUrl')):
                formats.append({
                    'url': live_info['liveUrl'],
                    'ext': 'mp4',
                    'protocol': 'm3u8_native',
                    'format_id': 'hls-fallback',
                    'vcodec': 'h264',
                    'quality': get_quality('origin'),
                })

        uploader = uploader or traverse_obj(live_info, ('ownerInfo', 'uniqueId'), ('owner', 'display_id'))

        return {
            'id': room_id,
            'uploader': uploader,
            'uploader_url': format_field(uploader, None, self._UPLOADER_URL_FORMAT) or None,
            'is_live': True,
            'formats': formats,
            '_format_sort_fields': ('quality', 'ext'),
            **traverse_obj(live_info, {
                'title': 'title',
                'uploader_id': (('ownerInfo', 'owner'), 'id', {str_or_none}),
                'creator': (('ownerInfo', 'owner'), 'nickname'),
                'concurrent_view_count': (('user_count', ('liveRoomStats', 'userCount')), {int_or_none}),
            }, get_all=False),
        }