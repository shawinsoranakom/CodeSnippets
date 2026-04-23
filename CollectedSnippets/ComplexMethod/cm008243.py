def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_data = self._download_json(
            f'https://um.viuapi.io/drm/v1/content/{display_id}', display_id, data=b'',
            headers={'Authorization': ViuOTTIndonesiaBaseIE._TOKEN, **self._HEADERS, 'ccode': 'ID'})
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(video_data['playUrl'], display_id)

        initial_state = self._search_json(
            r'window\.__INITIAL_STATE__\s*=', webpage, 'initial state',
            display_id)['content']['clipDetails']
        for key, url in initial_state.items():
            lang, ext = self._search_regex(
                r'^subtitle_(?P<lang>[\w-]+)_(?P<ext>\w+)$', key, 'subtitle metadata',
                default=(None, None), group=('lang', 'ext'))
            if lang and ext:
                subtitles.setdefault(lang, []).append({
                    'ext': ext,
                    'url': url,
                })

                if ext == 'vtt':
                    subtitles[lang].append({
                        'ext': 'srt',
                        'url': f'{remove_end(initial_state[key], "vtt")}srt',
                    })

        episode = traverse_obj(list(filter(
            lambda x: x.get('@type') in ('TVEpisode', 'Movie'), self._yield_json_ld(webpage, display_id))), 0) or {}
        return {
            'id': display_id,
            'title': (traverse_obj(initial_state, 'title', 'display_title')
                      or episode.get('name')),
            'description': initial_state.get('description') or episode.get('description'),
            'duration': initial_state.get('duration'),
            'thumbnail': traverse_obj(episode, ('image', 'url')),
            'timestamp': unified_timestamp(episode.get('dateCreated')),
            'formats': formats,
            'subtitles': subtitles,
            'episode_number': (traverse_obj(initial_state, 'episode_no', 'episodeno', expected_type=int_or_none)
                               or int_or_none(episode.get('episodeNumber'))),
            'cast': traverse_obj(episode, ('actor', ..., 'name'), default=None),
            'age_limit': self._AGE_RATINGS_MAPPER.get(initial_state.get('internal_age_rating')),
        }