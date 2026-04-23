def _real_extract(self, url):
        base, video_id = re.match(self._VALID_URL, url).groups()

        media = self._download_json(
            base + '.json', video_id, 'Downloading video JSON')

        if try_get(
                media,
                (lambda x: x['rights_management']['rights']['drm'],
                 lambda x: x['program_info']['rights_management']['rights']['drm']),
                dict):
            raise ExtractorError('This video is DRM protected.', expected=True)

        title = media['name']

        video = media['video']

        relinker_info = self._extract_relinker_info(video['content_url'], video_id)
        self._sort_formats(relinker_info['formats'])

        thumbnails = []
        for _, value in media.get('images', {}).items():
            if value:
                thumbnails.append({
                    'url': urljoin(url, value),
                })

        date_published = media.get('date_published')
        time_published = media.get('time_published')
        if date_published and time_published:
            date_published += ' ' + time_published

        subtitles = self._extract_subtitles(url, video)

        program_info = media.get('program_info') or {}
        season = media.get('season')

        info = {
            'id': remove_start(media.get('id'), 'ContentItem-') or video_id,
            'display_id': video_id,
            'title': self._live_title(title) if relinker_info.get(
                'is_live') else title,
            'alt_title': strip_or_none(media.get('subtitle')),
            'description': media.get('description'),
            'uploader': strip_or_none(media.get('channel')),
            'creator': strip_or_none(media.get('editor') or None),
            'duration': parse_duration(video.get('duration')),
            'timestamp': unified_timestamp(date_published),
            'thumbnails': thumbnails,
            'series': program_info.get('name'),
            'season_number': int_or_none(season),
            'season': season if (season and not season.isdigit()) else None,
            'episode': media.get('episode_title'),
            'episode_number': int_or_none(media.get('episode')),
            'subtitles': subtitles,
        }

        info.update(relinker_info)
        return info