def _real_extract(self, url):
        tenant, path = self._match_valid_url(url).group('tenant', 'id')
        qs = parse_qs(url)
        start_time = traverse_obj(qs, ('startTime', 0, {int_or_none}))
        stop_time = traverse_obj(qs, ('stopTime', 0, {int_or_none}))

        def livx_mode(mode):
            suffix = ''
            if mode == 'livess':
                suffix = '/manifest'
            elif mode == 'livehls':
                suffix = '/playlist.m3u8'
            file_qs = {}
            if start_time:
                file_qs['startTime'] = start_time
            if stop_time:
                file_qs['stopTime'] = stop_time
            if mode == 'nvr':
                file_qs['nolimit'] = 1
            elif mode != 'sc':
                file_qs['indexMode'] = 'true'
            return update_url_query(f'https://r.dcs.redcdn.pl/{mode}/o2/{tenant}/{path}.livx{suffix}', file_qs)

        # no id or title for a transmission. making ones up.
        title = path \
            .replace('/live', '').replace('live/', '') \
            .replace('/channel', '').replace('channel/', '') \
            .strip('/')
        video_id = join_nonempty(title.replace('/', '-'), start_time, stop_time)

        formats = []
        # downloading the manifest separately here instead of _extract_ism_formats to also get some stream metadata
        ism_res = self._download_xml_handle(
            livx_mode('livess'), video_id,
            note='Downloading ISM manifest',
            errnote='Failed to download ISM manifest',
            fatal=False)
        ism_doc = None
        if ism_res is not False:
            ism_doc, ism_urlh = ism_res
            formats, _ = self._parse_ism_formats_and_subtitles(ism_doc, ism_urlh.url, 'ss')

        nvr_urlh = self._request_webpage(
            HEADRequest(livx_mode('nvr')), video_id, 'Follow flv file redirect', fatal=False,
            expected_status=lambda _: True)
        if nvr_urlh and nvr_urlh.status == 200:
            formats.append({
                'url': nvr_urlh.url,
                'ext': 'flv',
                'format_id': 'direct-0',
                'preference': -1,   # might be slow
            })
        formats.extend(self._extract_mpd_formats(livx_mode('livedash'), video_id, mpd_id='dash', fatal=False))
        formats.extend(self._extract_m3u8_formats(
            livx_mode('livehls'), video_id, m3u8_id='hls', ext='mp4', fatal=False))

        time_scale = traverse_obj(ism_doc, ('@TimeScale', {int_or_none})) or 10000000
        duration = traverse_obj(
            ism_doc, ('@Duration', {float_or_none(scale=time_scale)})) or None

        live_status = None
        if traverse_obj(ism_doc, '@IsLive') == 'TRUE':
            live_status = 'is_live'
        elif duration:
            live_status = 'was_live'

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration,
            'live_status': live_status,
        }