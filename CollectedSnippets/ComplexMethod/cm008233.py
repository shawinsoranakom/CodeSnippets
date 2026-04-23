def _real_extract(self, url):
        domain, video_id = self._match_valid_url(url).groups()
        site = domain.split('.')[0]
        path = self._SITE_MAP.get(site, site)
        if path != 'series':
            path = 'migration/' + path
        video = self._download_json(
            f'https://globalcontent.corusappservices.com/templates/{path}/playlist/',
            video_id, query={'byId': video_id},
            headers={'Accept': 'application/json'})[0]
        title = video['title']

        formats = []
        for source in video.get('sources', []):
            smil_url = source.get('file')
            if not smil_url:
                continue
            source_type = source.get('type')
            note = 'Downloading{} smil file'.format(' ' + source_type if source_type else '')
            resp = self._download_webpage(
                smil_url, video_id, note, fatal=False,
                headers=self.geo_verification_headers())
            if not resp:
                continue
            error = self._parse_json(resp, video_id, fatal=False)
            if error:
                if error.get('exception') == 'GeoLocationBlocked':
                    self.raise_geo_restricted(countries=['CA'])
                raise ExtractorError(error['description'])
            smil = self._parse_xml(resp, video_id, fatal=False)
            if smil is None:
                continue
            namespace = self._parse_smil_namespace(smil)
            formats.extend(self._parse_smil_formats(
                smil, smil_url, video_id, namespace))
        if not formats and video.get('drm'):
            self.report_drm(video_id)

        subtitles = {}
        for track in video.get('tracks', []):
            track_url = track.get('file')
            if not track_url:
                continue
            lang = 'fr' if site in ('disneylachaine', 'seriesplus') else 'en'
            subtitles.setdefault(lang, []).append({'url': track_url})

        metadata = video.get('metadata') or {}
        get_number = lambda x: int_or_none(video.get('pl1$' + x) or metadata.get(x + 'Number'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': dict_get(video, ('defaultThumbnailUrl', 'thumbnail', 'image')),
            'description': video.get('description'),
            'timestamp': int_or_none(video.get('availableDate'), 1000),
            'subtitles': subtitles,
            'duration': float_or_none(metadata.get('duration')),
            'series': dict_get(video, ('show', 'pl1$show')),
            'season_number': get_number('season'),
            'episode_number': get_number('episode'),
        }