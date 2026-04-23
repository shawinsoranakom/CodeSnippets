def _real_extract(self, url):
        video_id, category = self._match_valid_url(url).group('id', 'category')
        webpage = self._download_webpage(url, video_id)

        hydration = self._search_json(
            r'window\.__RTVCPLAY_STATE__\s*=', webpage, 'hydration',
            video_id, transform_source=js_to_json)['content']['currentContent']

        asset_id = traverse_obj(hydration, ('video', 'assetid'))
        if asset_id:
            hls_url = hydration['base_url_hls'].replace('[node:field_asset_id]', asset_id)
        else:
            hls_url = traverse_obj(hydration, ('channel', 'hls'))

        metadata = traverse_obj(hydration, {
            'title': 'title',
            'description': 'description',
            'thumbnail': ((('channel', 'image', 'logo'), ('resource', 'image', 'cover_desktop')), 'path'),
        }, get_all=False)

        # Probably it's a program's page
        if not hls_url:
            seasons = traverse_obj(
                hydration, ('widgets', lambda _, y: y['type'] == 'seasonList', 'contents'),
                get_all=False)
            if not seasons:
                podcast_episodes = hydration.get('audios')
                if not podcast_episodes:
                    raise ExtractorError('Could not find asset_id nor program playlist nor podcast episodes')

                return self.playlist_result([
                    self.url_result(episode['file'], url_transparent=True, **traverse_obj(episode, {
                        'title': 'title',
                        'description': ('description', {clean_html}),
                        'episode_number': ('chapter_number', {float_or_none}, {int_or_none}),
                        'season_number': ('season', {int_or_none}),
                    })) for episode in podcast_episodes], video_id, **metadata)

            entries = [self.url_result(
                urljoin(url, episode['slug']), url_transparent=True,
                **traverse_obj(season, {
                    'season': 'title',
                    'season_number': ('season', {int_or_none}),
                }), **traverse_obj(episode, {
                    'title': 'title',
                    'thumbnail': ('image', 'cover', 'path'),
                    'episode_number': ('chapter_number', {int_or_none}),
                })) for season in seasons for episode in traverse_obj(season, ('contents', ...))]

            return self.playlist_result(entries, video_id, **metadata)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(hls_url, video_id, 'mp4')

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': category == 'en-vivo',
            **metadata,
        }