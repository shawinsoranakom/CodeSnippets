def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = self._EPISODE_BASE_URL + display_id

        try:
            m3u8_url = self._download_json(
                api_episode_url + '/videos', display_id,
                'Downloading video JSON metadata')['data'][0]['attributes']['url']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                if self._parse_json(e.cause.read().decode(), display_id).get('access') is False:
                    self.raise_login_required(
                        '%s is only available for FIRST members' % display_id)
            raise

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        episode = self._download_json(
            api_episode_url, display_id,
            'Downloading episode JSON metadata')['data'][0]
        attributes = episode['attributes']
        title = attributes.get('title') or attributes['display_title']
        video_id = compat_str(episode['id'])

        thumbnails = []
        for image in episode.get('included', {}).get('images', []):
            if image.get('type') == 'episode_image':
                img_attributes = image.get('attributes') or {}
                for k in ('thumb', 'small', 'medium', 'large'):
                    img_url = img_attributes.get(k)
                    if img_url:
                        thumbnails.append({
                            'id': k,
                            'url': img_url,
                        })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': attributes.get('description') or attributes.get('caption'),
            'thumbnails': thumbnails,
            'series': attributes.get('show_title'),
            'season_number': int_or_none(attributes.get('season_number')),
            'season_id': attributes.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(attributes.get('number')),
            'episode_id': str_or_none(episode.get('uuid')),
            'formats': formats,
            'channel_id': attributes.get('channel_id'),
            'duration': int_or_none(attributes.get('length')),
        }