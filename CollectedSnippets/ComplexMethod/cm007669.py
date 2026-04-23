def _real_extract(self, url):
        video_id = self._match_id(url)

        player = try_get((self._download_json(
            'https://frontend.vh.yandex.ru/graphql', video_id, data=('''{
  player(content_id: "%s") {
    computed_title
    content_url
    description
    dislikes
    duration
    likes
    program_title
    release_date
    release_date_ut
    release_year
    restriction_age
    season
    start_time
    streams
    thumbnail
    title
    views_count
  }
}''' % video_id).encode(), fatal=False)), lambda x: x['player']['content'])
        if not player or player.get('error'):
            player = self._download_json(
                'https://frontend.vh.yandex.ru/v23/player/%s.json' % video_id,
                video_id, query={
                    'stream_options': 'hires',
                    'disable_trackings': 1,
                })
        content = player['content']

        title = content.get('title') or content['computed_title']

        formats = []
        streams = content.get('streams') or []
        streams.append({'url': content.get('content_url')})
        for stream in streams:
            content_url = url_or_none(stream.get('url'))
            if not content_url:
                continue
            ext = determine_ext(content_url)
            if ext == 'ismc':
                continue
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    content_url, video_id, 'mp4',
                    'm3u8_native', m3u8_id='hls', fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    content_url, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({'url': content_url})

        self._sort_formats(formats)

        timestamp = (int_or_none(content.get('release_date'))
                     or int_or_none(content.get('release_date_ut'))
                     or int_or_none(content.get('start_time')))
        season = content.get('season') or {}

        return {
            'id': video_id,
            'title': title,
            'description': content.get('description'),
            'thumbnail': content.get('thumbnail'),
            'timestamp': timestamp,
            'duration': int_or_none(content.get('duration')),
            'series': content.get('program_title'),
            'age_limit': int_or_none(content.get('restriction_age')),
            'view_count': int_or_none(content.get('views_count')),
            'like_count': int_or_none(content.get('likes')),
            'dislike_count': int_or_none(content.get('dislikes')),
            'season_number': int_or_none(season.get('season_number')),
            'season_id': season.get('id'),
            'release_year': int_or_none(content.get('release_year')),
            'formats': formats,
        }