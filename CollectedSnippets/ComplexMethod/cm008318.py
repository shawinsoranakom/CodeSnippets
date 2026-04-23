def _extract_formats(self, api_data, video_id):
        fmt_filter = lambda _, v: v['isAvailable'] and v['id']
        videos = traverse_obj(api_data, ('media', 'domand', 'videos', fmt_filter))
        audios = traverse_obj(api_data, ('media', 'domand', 'audios', fmt_filter))
        access_key = traverse_obj(api_data, ('media', 'domand', 'accessRightKey', {str}))
        track_id = traverse_obj(api_data, ('client', 'watchTrackId', {str}))
        if not all((videos, audios, access_key, track_id)):
            return

        m3u8_url = self._download_json(
            f'{self._API_BASE}/v1/watch/{video_id}/access-rights/hls',
            video_id, headers={
                'Accept': 'application/json;charset=utf-8',
                'Content-Type': 'application/json',
                'X-Access-Right-Key': access_key,
                'X-Request-With': self._BASE_URL,
                **self._HEADERS,
            }, query={
                'actionTrackId': track_id,
            }, data=json.dumps({
                'outputs': list(itertools.product((v['id'] for v in videos), (a['id'] for a in audios))),
            }).encode(),
        )['data']['contentUrl']
        raw_fmts = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')

        formats = []
        for a_fmt in traverse_obj(raw_fmts, lambda _, v: v['vcodec'] == 'none'):
            formats.append({
                **a_fmt,
                **traverse_obj(audios, (lambda _, v: a_fmt['format_id'].startswith(v['id']), {
                    'abr': ('bitRate', {float_or_none(scale=1000)}),
                    'asr': ('samplingRate', {int_or_none}),
                    'format_id': ('id', {str}),
                    'quality': ('qualityLevel', {int_or_none}),
                }, any)),
                'acodec': 'aac',
            })

        # Sort first, keeping the lowest-tbr formats
        v_fmts = sorted((fmt for fmt in raw_fmts if fmt['vcodec'] != 'none'), key=lambda f: f['tbr'])
        self._remove_duplicate_formats(v_fmts)
        # Calculate the true vbr/tbr by subtracting the lowest abr
        min_abr = traverse_obj(audios, (..., 'bitRate', {float_or_none(scale=1000)}, all, {min})) or 0
        for v_fmt in v_fmts:
            v_fmt['format_id'] = url_basename(v_fmt['url']).rpartition('.')[0]
            v_fmt['quality'] = traverse_obj(videos, (
                lambda _, v: v['id'] == v_fmt['format_id'], 'qualityLevel', {int_or_none}, any)) or -1
            v_fmt['tbr'] -= min_abr
        formats.extend(v_fmts)

        return formats