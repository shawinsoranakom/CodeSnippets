def _real_extract(self, url):
        video_id, video_type = self._match_valid_url(url).group('id', 'type')
        webpage = self._download_webpage(f'https://tubitv.com/{video_type}/{video_id}/', video_id)
        video_data = self._search_json(
            r'window\.__data\s*=', webpage, 'data', video_id,
            transform_source=js_to_json)['video']['byId'][video_id]

        formats = []
        drm_formats = False

        for resource in traverse_obj(video_data, ('video_resources', lambda _, v: url_or_none(v['manifest']['url']))):
            resource_type = resource.get('type')
            manifest_url = resource['manifest']['url']
            if resource_type == 'dash':
                formats.extend(self._extract_mpd_formats(manifest_url, video_id, mpd_id=resource_type, fatal=False))
            elif resource_type in ('hlsv3', 'hlsv6'):
                formats.extend(self._extract_m3u8_formats(manifest_url, video_id, 'mp4', m3u8_id=resource_type, fatal=False))
            elif resource_type in self._UNPLAYABLE_FORMATS:
                drm_formats = True
            else:
                self.report_warning(f'Skipping unknown resource type "{resource_type}"')

        if not formats and drm_formats:
            self.report_drm(video_id)
        elif not formats and not video_data.get('policy_match'):  # policy_match is False if content was removed
            raise ExtractorError('This content is currently unavailable', expected=True)

        subtitles = {}
        for sub in traverse_obj(video_data, ('subtitles', lambda _, v: url_or_none(v['url']))):
            subtitles.setdefault(sub.get('lang', 'English'), []).append({
                'url': self._proto_relative_url(sub['url']),
            })

        title = traverse_obj(video_data, ('title', {str}))
        season_number, episode_number, episode_title = self._search_regex(
            r'^S(\d+):E(\d+) - (.+)', title, 'episode info', fatal=False, group=(1, 2, 3), default=(None, None, None))

        return {
            'id': video_id,
            'title': strip_or_none(title),
            'formats': formats,
            'subtitles': subtitles,
            'season_number': int_or_none(season_number),
            'episode_number': int_or_none(episode_number),
            'episode': strip_or_none(episode_title),
            **traverse_obj(video_data, {
                'description': ('description', {str}),
                'duration': ('duration', {int_or_none}),
                'uploader_id': ('publisher_id', {str}),
                'release_year': ('year', {int_or_none}),
                'thumbnails': ('thumbnails', ..., {url_or_none}, {'url': {self._proto_relative_url}}),
            }),
        }