def _real_extract(self, url):
        ref_id, display_id = self._match_valid_url(url).groups()
        webpage = self._download_webpage(url, display_id)
        app_token = self._search_regex([
            r'clientAPI\s*:\s*"([^"]+)"',
            r'data-de-api-key\s*=\s*"([^"]+)"',
        ], webpage, 'app token')
        query = {'refid': ref_id, 'prefid': display_id} if ref_id else {'v': display_id}
        program = self._call_api(
            app_token, 'program', display_id, query, url)['WsProgramResponse']['program']
        video_id = program['uuid']
        video_data = program['asset']
        title = video_data['title']
        asset_type = dict_get(video_data, ['assetType', 'asset_type'])

        formats = []

        def process_asset_file(asset_file):
            if not asset_file:
                return
            # TODO: extract rtmp formats
            http_url = asset_file.get('http_url')
            if not http_url:
                return
            tbr = None
            vbr = int_or_none(asset_file.get('videoBitrate'), 1024)
            abr = int_or_none(asset_file.get('audioBitrate'), 1024)
            if asset_type == 'video':
                tbr = vbr + abr
            elif asset_type == 'audio':
                tbr = abr

            formats.append({
                'format_id': join_nonempty('http', tbr),
                'url': unescapeHTML(http_url),
                'vbr': vbr,
                'abr': abr,
                'width': int_or_none(asset_file.get('videoWidth')),
                'height': int_or_none(asset_file.get('videoHeight')),
                'filesize': int_or_none(asset_file.get('filesize')),
                'tbr': tbr,
            })

        def process_asset_files(asset_files):
            for asset_file in (asset_files or []):
                process_asset_file(asset_file)

        process_asset_files(video_data.get('assetFiles'))
        process_asset_file(video_data.get('referenceFile'))
        if not formats:
            asset_id = video_data.get('assetid') or program.get('assetid')
            if asset_id:
                process_asset_files(try_get(self._call_api(
                    app_token, 'asset_file', display_id, {
                        'assetid': asset_id,
                    }, url, False), lambda x: x['WsAssetFileResponse']['AssetFiles']))

        m3u8_url = dict_get(video_data, [
            'm3u8iPadURL',
            'ipadM3u8Url',
            'm3u8AndroidURL',
            'm3u8iPhoneURL',
            'iphoneM3u8Url'])
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        smil_url = dict_get(video_data, ['httpSmil', 'hdSmil', 'rtmpSmil'])
        if smil_url:
            transform_source = lambda x: x.replace('src="/', 'src="')
            if ref_id == 'nhkworld':
                # TODO: figure out if this is something to be fixed in urljoin,
                # _parse_smil_formats or keep it here
                transform_source = lambda x: x.replace('src="/', 'src="').replace('/media"', '/media/"')
            formats.extend(self._extract_smil_formats(
                re.sub(r'/od/[^/]+/', '/od/http/', smil_url), video_id,
                transform_source=transform_source, fatal=False))

        subtitles = {}
        for caption in video_data.get('captions', []):
            caption_url = caption.get('url')
            if caption_url:
                subtitles.setdefault(caption.get('locale', 'en'), []).append({
                    'url': caption_url})

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailUrl'),
            'timestamp': parse_iso8601(video_data.get('dateadd')),
            'formats': formats,
            'subtitles': subtitles,
            '_format_sort_fields': ('tbr', ),  # Incomplete resolution information
        }