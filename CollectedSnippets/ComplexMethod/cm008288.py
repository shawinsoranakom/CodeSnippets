def _real_extract(self, url):
        video_id = self._match_id(url)
        formats, subtitles = self._extract_smil_formats_and_subtitles(
            update_url_query(f'{self._PLAYER_API}/video_smil', {'id': video_id}), video_id)

        if not formats:
            urlh = self._request_webpage(
                HEADRequest('https://sbs-vod-prod-01.akamaized.net/'), video_id,
                note='Checking geo-restriction', fatal=False, expected_status=403)
            if urlh:
                error_reasons = urlh.headers.get_all('x-error-reason') or []
                if 'geo-blocked' in error_reasons:
                    self.raise_geo_restricted(countries=['AU'])
            self.raise_no_formats('No formats are available', video_id=video_id)

        media = traverse_obj(self._download_json(
            f'{self._PLAYER_API}/video_stream', video_id, fatal=False,
            query={'id': video_id, 'context': 'tv'}), ('video_object', {dict})) or {}

        media.update(self._download_json(
            f'https://catalogue.pr.sbsod.com/mpx-media/{video_id}',
            video_id, fatal=not media) or {})

        # For named episodes, use the catalogue's title to set episode, rather than generic 'Episode N'.
        if traverse_obj(media, ('partOfSeries', {dict})):
            media['epName'] = traverse_obj(media, ('title', {str}))

        # Need to set different language for forced subs or else they have priority over full subs
        fixed_subtitles = {}
        for lang, subs in subtitles.items():
            for sub in subs:
                fixed_lang = lang
                if sub['url'].lower().endswith('_fe.vtt'):
                    fixed_lang += '-forced'
                fixed_subtitles.setdefault(fixed_lang, []).append(sub)

        return {
            'id': video_id,
            **traverse_obj(media, {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'channel': ('taxonomy', 'channel', 'name', {str}),
                'series': ((('partOfSeries', 'name'), 'seriesTitle'), {str}),
                'series_id': ((('partOfSeries', 'uuid'), 'seriesID'), {str}),
                'season_number': ('seasonNumber', {int_or_none}),
                'episode': ('epName', {str}),
                'episode_number': ('episodeNumber', {int_or_none}),
                'timestamp': (('datePublished', ('publication', 'startDate')), {parse_iso8601}),
                'release_year': ('releaseYear', {int_or_none}),
                'duration': ('duration', ({float_or_none}, {parse_duration})),
                'is_live': ('liveStream', {bool}),
                'age_limit': (
                    ('classificationID', 'contentRating'), {str.upper}, {self._AUS_TV_PARENTAL_GUIDELINES.get}),
            }, get_all=False),
            **traverse_obj(media, {
                'categories': (('genres', ...), ('taxonomy', ('genre', 'subgenre'), 'name'), {str}),
                'tags': (('consumerAdviceTexts', ('sbsSubCertification', 'consumerAdvice')), ..., {str}),
                'thumbnails': ('thumbnails', lambda _, v: url_or_none(v['contentUrl']), {
                    'id': ('name', {str}),
                    'url': 'contentUrl',
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                }),
            }),
            'formats': formats,
            'subtitles': fixed_subtitles,
            'uploader': 'SBSC',
        }