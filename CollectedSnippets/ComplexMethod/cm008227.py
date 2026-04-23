def _real_extract(self, url):
        display_id, video_id = self._match_valid_url(url).groups()

        metadata_url = self._download_json(
            self._API_BASE + 'client/v1/url', video_id, 'Downloading API endpoint data',
            query={'href': urllib.parse.urlparse(url).path})['href']
        metadata = self._download_json(metadata_url, video_id)

        try:
            video_data = self._download_json(metadata['urlVideo'], video_id, 'Downloading video data')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                error = self._parse_json(e.cause.response.read(), None)
                if error.get('error') == 'required_registered':
                    self.raise_login_required()
                raise ExtractorError(error['error_description'], expected=True)
            raise

        formats = []
        subtitles = {}
        for source in traverse_obj(video_data, ('sources', lambda _, v: url_or_none(v['src']))):
            src_url = source['src']
            src_type = source.get('type')
            if src_type in ('application/vnd.apple.mpegurl', 'application/hls+legacy', 'application/hls+hevc'):
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            elif src_type in ('application/dash+xml', 'application/dash+hevc'):
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    src_url, video_id, mpd_id='dash', fatal=False)
            else:
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'display_id': display_id,
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video_data, {
                'title': ('titulo', {str}),
                'description': ('descripcion', {str}),
                'duration': ('duration', {int_or_none}),
                'thumbnail': ('imgPoster', {url_or_none}, {lambda v: f'{v}1920x1080.jpg'}),
                'age_limit': ('ageRating', {parse_age_limit}),
            }),
            **traverse_obj(metadata, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'duration': ('duration', {int_or_none}),
                'tags': ('tags', ..., 'title', {str}),
                'age_limit': ('ageRating', {parse_age_limit}),
                'series': ('format', 'title', {str}),
                'season': ('currentSeason', 'title', {str}),
                'season_number': ('currentSeason', 'seasonNumber', {int_or_none}),
                'episode_number': ('numberOfEpisode', {int_or_none}),
                'timestamp': ('publicationDate', {int_or_none(scale=1000)}),
                'channel': ('channel', 'title', {str}),
            }),
        }