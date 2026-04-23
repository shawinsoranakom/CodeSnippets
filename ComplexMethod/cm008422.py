def _real_extract(self, url):
        base, video_id = self._match_valid_url(url).groups()

        media = self._download_json(
            f'{base}.json', video_id, 'Downloading video JSON')

        if traverse_obj(media, ('rights_management', 'rights', 'drm')):
            self.report_drm(video_id)

        video = media['video']
        relinker_info = self._extract_relinker_info(video['content_url'], video_id)
        date_published = join_nonempty(
            media.get('date_published'), media.get('time_published'), delim=' ')
        season = media.get('season')
        alt_title = join_nonempty(media.get('subtitle'), media.get('toptitle'), delim=' - ')

        return {
            'id': remove_start(media.get('id'), 'ContentItem-') or video_id,
            'display_id': video_id,
            'title': media.get('name'),
            'alt_title': strip_or_none(alt_title or None),
            'description': media.get('description'),
            'uploader': strip_or_none(
                traverse_obj(media, ('program_info', 'channel'))
                or media.get('channel') or None),
            'creator': strip_or_none(
                traverse_obj(media, ('program_info', 'editor'))
                or media.get('editor') or None),
            'duration': parse_duration(video.get('duration')),
            'timestamp': unified_timestamp(date_published),
            'thumbnails': self._get_thumbnails_list(media.get('images'), url),
            'series': traverse_obj(media, ('program_info', 'name')),
            'season_number': int_or_none(season),
            'season': season if (season and not season.isdigit()) else None,
            'episode': media.get('episode_title'),
            'episode_number': int_or_none(media.get('episode')),
            'subtitles': self._extract_subtitles(url, video),
            'release_year': int_or_none(traverse_obj(media, ('track_info', 'edit_year'))),
            **relinker_info,
        }