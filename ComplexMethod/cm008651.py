def _real_extract(self, url):
        m = self._match_valid_url(url)
        video_id = m.group('id')

        # some sites use this embed format (see: https://github.com/ytdl-org/youtube-dl/issues/2990)
        if m.group('type') == 'embed/recorded':
            video_id = m.group('id')
            desktop_url = 'http://www.ustream.tv/recorded/' + video_id
            return self.url_result(desktop_url, 'Ustream')
        if m.group('type') == 'embed':
            video_id = m.group('id')
            webpage = self._download_webpage(url, video_id)
            content_video_ids = self._parse_json(self._search_regex(
                r'ustream\.vars\.offAirContentVideoIds=([^;]+);', webpage,
                'content video IDs'), video_id)
            return self.playlist_result(
                (self.url_result('http://www.ustream.tv/recorded/' + u, 'Ustream') for u in content_video_ids),
                video_id)

        params = self._download_json(
            f'https://api.ustream.tv/videos/{video_id}.json', video_id)

        error = params.get('error')
        if error:
            raise ExtractorError(
                f'{self.IE_NAME} returned error: {error}', expected=True)

        video = params['video']

        title = video['title']
        filesize = float_or_none(video.get('file_size'))

        formats = [{
            'id': video_id,
            'url': video_url,
            'ext': format_id,
            'filesize': filesize,
        } for format_id, video_url in video['media_urls'].items() if video_url]

        if not formats:
            hls_streams = self._get_streams(url, video_id, app_id_ver=(11, 2))
            if hls_streams:
                # m3u8_native leads to intermittent ContentTooShortError
                formats.extend(self._extract_m3u8_formats(
                    hls_streams[0]['url'], video_id, ext='mp4', m3u8_id='hls'))

            '''
            # DASH streams handling is incomplete as 'url' is missing
            dash_streams = self._get_streams(url, video_id, app_id_ver=(3, 1))
            if dash_streams:
                formats.extend(self._parse_segmented_mp4(dash_streams))
            '''

        description = video.get('description')
        timestamp = int_or_none(video.get('created_at'))
        duration = float_or_none(video.get('length'))
        view_count = int_or_none(video.get('views'))

        uploader = video.get('owner', {}).get('username')
        uploader_id = video.get('owner', {}).get('id')

        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail_url,
        } for thumbnail_id, thumbnail_url in video.get('thumbnail', {}).items()]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
        }