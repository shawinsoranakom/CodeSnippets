def _real_extract(self, url):
        url_slug = self._match_id(url)
        webpage = self._download_webpage(url, url_slug)

        json_data = self._search_json(
            r'window\.__data\s*=', webpage, 'data', url_slug, fatal=False) or {}
        item = traverse_obj(
            json_data, ('cache', 'page', ..., (None, ('entries', 0)), 'item', {dict}), get_all=False)
        if item:
            item_id = item.get('id')
        else:
            item_id = url_slug.rsplit('_', 1)[-1]
            item = self._download_json(
                f'https://production-cdn.dr-massive.com/api/items/{item_id}', item_id,
                note='Attempting to download backup item data', query={
                    'device': 'web_browser',
                    'expand': 'all',
                    'ff': 'idp,ldp,rpt',
                    'geoLocation': 'dk',
                    'isDeviceAbroad': 'false',
                    'lang': 'da',
                    'segments': 'drtv,optedout',
                    'sub': 'Anonymous',
                })

        video_id = try_call(lambda: item['customId'].rsplit(':', 1)[-1]) or item_id
        stream_data = self._download_json(
            f'https://production.dr-massive.com/api/account/items/{item_id}/videos', video_id,
            note='Downloading stream data', query={
                'delivery': 'stream',
                'device': 'web_browser',
                'ff': 'idp,ldp,rpt',
                'lang': 'da',
                'resolution': 'HD-1080',
                'sub': 'Anonymous',
            }, headers={'authorization': f'Bearer {self._TOKEN}'})

        formats = []
        subtitles = {}
        for stream in traverse_obj(stream_data, (lambda _, x: x['url'])):
            format_id = stream.get('format', 'na')
            access_service = stream.get('accessService')
            preference = None
            subtitle_suffix = ''
            if access_service in ('SpokenSubtitles', 'SignLanguage', 'VisuallyInterpreted'):
                preference = -1
                format_id += f'-{access_service}'
                subtitle_suffix = f'-{access_service}'
            elif access_service == 'StandardVideo':
                preference = 1
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                stream.get('url'), video_id, ext='mp4', preference=preference, m3u8_id=format_id, fatal=False)
            formats.extend(fmts)

            api_subtitles = traverse_obj(stream, ('subtitles', lambda _, v: url_or_none(v['link']), {dict}))
            if not api_subtitles:
                self._merge_subtitles(subs, target=subtitles)

            for sub_track in api_subtitles:
                lang = sub_track.get('language') or 'da'
                subtitles.setdefault(self.SUBTITLE_LANGS.get(lang, lang) + subtitle_suffix, []).append({
                    'url': sub_track['link'],
                    'ext': mimetype2ext(sub_track.get('format')) or 'vtt',
                })

        if not formats and traverse_obj(item, ('season', 'customFields', 'IsGeoRestricted')):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(item, {
                'title': 'title',
                'alt_title': 'contextualTitle',
                'description': 'description',
                'thumbnail': ('images', 'wallpaper'),
                'release_timestamp': ('customFields', 'BroadcastTimeDK', {parse_iso8601}),
                'duration': ('duration', {int_or_none}),
                'series': ('season', 'show', 'title'),
                'season': ('season', 'title'),
                'season_number': ('season', 'seasonNumber', {int_or_none}),
                'season_id': 'seasonId',
                'episode': 'episodeName',
                'episode_number': ('episodeNumber', {int_or_none}),
                'release_year': ('releaseYear', {int_or_none}),
            }),
        }