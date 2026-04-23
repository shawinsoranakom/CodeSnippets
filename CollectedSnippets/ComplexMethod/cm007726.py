def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})

        video_id = self._match_id(url)

        noplaylist = self._downloader.params.get('noplaylist')
        noplaylist_prompt = True
        if 'force_noplaylist' in data:
            noplaylist = data['force_noplaylist']
            noplaylist_prompt = False

        webpage = self._download_webpage(url, video_id)

        program_info = self._parse_json(self._search_regex(
            r'var\s+programInfo\s*=\s*([^;]+)', webpage, 'VOD data', default='{}'),
            video_id)

        season_list = list(program_info.get('seasonList', {}).values())
        if season_list:
            if not noplaylist:
                return self._extract_playlist(
                    season_list[0], video_id, program_info,
                    prompt=noplaylist_prompt)

            if noplaylist_prompt:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        # In browsers `getMainUrl` request is always issued. Usually this
        # endpoint gives the same result as the data embedded in the webpage.
        # If georestricted, there are no embedded data, so an extra request is
        # necessary to get the error code
        if 'assetId' not in program_info:
            program_info = self._download_json(
                'https://www.litv.tv/vod/ajax/getProgramInfo', video_id,
                query={'contentId': video_id},
                headers={'Accept': 'application/json'})
        video_data = self._parse_json(self._search_regex(
            r'uiHlsUrl\s*=\s*testBackendData\(([^;]+)\);',
            webpage, 'video data', default='{}'), video_id)
        if not video_data:
            payload = {
                'assetId': program_info['assetId'],
                'watchDevices': program_info['watchDevices'],
                'contentType': program_info['contentType'],
            }
            video_data = self._download_json(
                'https://www.litv.tv/vod/getMainUrl', video_id,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'})

        if not video_data.get('fullpath'):
            error_msg = video_data.get('errorMessage')
            if error_msg == 'vod.error.outsideregionerror':
                self.raise_geo_restricted('This video is available in Taiwan only')
            if error_msg:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, error_msg), expected=True)
            raise ExtractorError('Unexpected result from %s' % self.IE_NAME)

        formats = self._extract_m3u8_formats(
            video_data['fullpath'], video_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        for a_format in formats:
            # LiTV HLS segments doesn't like compressions
            a_format.setdefault('http_headers', {})['Youtubedl-no-compression'] = True

        title = program_info['title'] + program_info.get('secondaryMark', '')
        description = program_info.get('description')
        thumbnail = program_info.get('imageFile')
        categories = [item['name'] for item in program_info.get('category', [])]
        episode = int_or_none(program_info.get('episode'))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'episode_number': episode,
        }