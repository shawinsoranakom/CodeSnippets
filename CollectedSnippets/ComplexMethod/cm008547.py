def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        vod_data = self._search_nextjs_data(webpage, video_id)['props']['pageProps']

        program_info = traverse_obj(vod_data, ('programInformation', {dict})) or {}
        playlist_data = traverse_obj(vod_data, ('seriesTree'))
        if playlist_data and self._yes_playlist(program_info.get('series_id'), video_id, smuggled_data):
            return self._extract_playlist(playlist_data, program_info.get('content_type'))

        asset_id = traverse_obj(program_info, ('assets', 0, 'asset_id', {str}))
        if asset_id:  # This is a VOD
            media_type = 'vod'
        else:  # This is a live stream
            asset_id = program_info['content_id']
            media_type = program_info['content_type']
        puid = try_call(lambda: self._get_cookies('https://www.litv.tv/')['PUID'].value)
        if puid:
            endpoint = 'get-urls'
        else:
            puid = str(uuid.uuid4())
            endpoint = 'get-urls-no-auth'
        video_data = self._download_json(
            f'https://www.litv.tv/api/{endpoint}', video_id,
            data=json.dumps({'AssetId': asset_id, 'MediaType': media_type, 'puid': puid}).encode(),
            headers={'Content-Type': 'application/json'})

        if error := traverse_obj(video_data, ('error', {dict})):
            error_msg = traverse_obj(error, ('message', {str}))
            if error_msg and 'OutsideRegionError' in error_msg:
                self.raise_geo_restricted('This video is available in Taiwan only')
            elif error_msg:
                raise ExtractorError(f'{self.IE_NAME} said: {error_msg}', expected=True)
            raise ExtractorError(f'Unexpected error from {self.IE_NAME}')

        formats = self._extract_m3u8_formats(
            video_data['result']['AssetURLs'][0], video_id, ext='mp4', m3u8_id='hls')
        for a_format in formats:
            # LiTV HLS segments doesn't like compressions
            a_format.setdefault('http_headers', {})['Accept-Encoding'] = 'identity'

        return {
            'id': video_id,
            'formats': formats,
            'title': join_nonempty('title', 'secondary_mark', delim='', from_dict=program_info),
            **traverse_obj(program_info, {
                'description': ('description', {str}),
                'thumbnail': ('picture', {urljoin('https://p-cdnstatic.svc.litv.tv/')}),
                'categories': ('genres', ..., 'name', {str}),
                'episode_number': ('episode', {int_or_none}),
            }),
        }