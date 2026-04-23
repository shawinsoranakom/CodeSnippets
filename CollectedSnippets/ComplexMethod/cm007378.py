def _parse_episode(self, episode):
        episode_id = episode['id']
        title = episode['title'].strip()
        audio_file = episode.get('audio_file') or {}
        audio_file_url = audio_file.get('url') or episode.get('audio_file_url') or episode['enclosure_url']

        season = episode.get('season') or {}
        season_href = season.get('href')
        season_id = None
        if season_href:
            season_id = self._search_regex(
                r'https?://api.simplecast.com/seasons/(%s)' % self._UUID_REGEX,
                season_href, 'season id', default=None)

        webpage_url = episode.get('episode_url')
        channel_url = None
        if webpage_url:
            channel_url = self._search_regex(
                r'(https?://[^/]+\.simplecast\.com)',
                webpage_url, 'channel url', default=None)

        return {
            'id': episode_id,
            'display_id': episode.get('slug'),
            'title': title,
            'url': clean_podcast_url(audio_file_url),
            'webpage_url': webpage_url,
            'channel_url': channel_url,
            'series': try_get(episode, lambda x: x['podcast']['title']),
            'season_number': int_or_none(season.get('number')),
            'season_id': season_id,
            'thumbnail': episode.get('image_url'),
            'episode_id': episode_id,
            'episode_number': int_or_none(episode.get('number')),
            'description': strip_or_none(episode.get('description')),
            'timestamp': parse_iso8601(episode.get('published_at')),
            'duration': int_or_none(episode.get('duration')),
            'filesize': int_or_none(audio_file.get('size') or episode.get('audio_file_size')),
        }