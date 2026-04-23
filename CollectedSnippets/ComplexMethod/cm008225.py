def _real_extract(self, url):
        slug, display_id = self._match_valid_url(url).group('slug', 'id')
        movie_data = self._download_json(
            f'https://api.brainpop.com/api/content/published/bp/en/{slug}/movie?full=1', display_id,
            'Downloading movie data JSON', 'Unable to download movie data')['data']
        topic_data = traverse_obj(self._download_json(
            f'https://api.brainpop.com/api/content/published/bp/en/{slug}?full=1', display_id,
            'Downloading topic data JSON', 'Unable to download topic data', fatal=False),
            ('data', 'topic'), expected_type=dict) or movie_data['topic']

        if not traverse_obj(movie_data, ('access', 'allow')):
            reason = traverse_obj(movie_data, ('access', 'reason'))
            if 'logged' in reason:
                self.raise_login_required(reason, metadata_available=True)
            else:
                self.raise_no_formats(reason, video_id=display_id)
        movie_feature = movie_data['feature']
        movie_feature_data = movie_feature['data']

        formats, subtitles = [], {}
        formats.extend(self._extract_adaptive_formats(movie_feature_data, movie_feature_data.get('token', ''), display_id, '%s_v2', {
            'language': movie_feature.get('language') or 'en',
            'language_preference': 10,
        }))
        for lang, localized_feature in traverse_obj(movie_feature, 'localization', default={}, expected_type=dict).items():
            formats.extend(self._extract_adaptive_formats(localized_feature, localized_feature.get('token', ''), display_id, '%s_v2', {
                'language': lang,
                'language_preference': -10,
            }))

        # TODO: Do localization fields also have subtitles?
        for name, url in movie_feature_data.items():
            lang = self._search_regex(
                r'^subtitles_(?P<lang>\w+)$', name, 'subtitle metadata', default=None)
            if lang and url:
                subtitles.setdefault(lang, []).append({
                    'url': urljoin(self._CDN_URL, url),
                })

        return {
            'id': topic_data['topic_id'],
            'display_id': display_id,
            'title': topic_data.get('name'),
            'description': topic_data.get('synopsis'),
            'formats': formats,
            'subtitles': subtitles,
        }