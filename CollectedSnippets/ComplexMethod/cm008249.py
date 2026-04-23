def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = f'{self._API_BASE_URL}/watch/{display_id}'

        try:
            video_data = self._download_json(
                api_episode_url + '/videos', display_id, 'Downloading video JSON metadata',
                headers={'Client-Type': 'web'})['data'][0]  # web client-type yields ad-free streams
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                if self._parse_json(e.cause.response.read().decode(), display_id).get('access') is False:
                    self.raise_login_required(
                        f'{display_id} is only available for FIRST members')
            raise

        # XXX: additional ad-free URL at video_data['links']['download'] but often gives 403 errors
        m3u8_url = video_data['attributes']['url']
        is_brightcove = traverse_obj(video_data, ('attributes', 'encoding_pipeline')) == 'brightcove'
        bc_id = traverse_obj(video_data, ('attributes', 'uid', {str}))

        try:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls')
        except ExtractorError as e:
            if is_brightcove and bc_id and isinstance(e.cause, HTTPError) and e.cause.status == 403:
                self.report_warning(
                    'Direct m3u8 URL returned HTTP Error 403; retrying with Brightcove extraction')
                formats, subtitles = self._extract_brightcove_formats_and_subtitles(bc_id, url, m3u8_url)
            else:
                raise

        episode = self._download_json(
            api_episode_url, display_id,
            'Downloading episode JSON metadata')['data'][0]

        return {
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            **self._extract_video_info(episode),
        }