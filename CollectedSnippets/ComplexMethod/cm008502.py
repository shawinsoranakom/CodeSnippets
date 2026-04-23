def _real_extract(self, url):
        video_id, video_type = self._match_valid_url(url).group('id', 'type')
        backend = self._configuration_arg('backend', ['streaks'])[0]
        if backend not in ('brightcove', 'streaks'):
            raise ExtractorError(f'Invalid backend value: {backend}', expected=True)

        if video_type == 'series':
            series_info = self._call_platform_api(
                f'v2/callSeries/{video_id}', video_id, 'Downloading series info')
            return self.playlist_from_matches(
                self._yield_episode_ids_for_series(video_id), video_id,
                traverse_obj(series_info, ('result', 'content', 'content', 'title', {str})),
                ie=TVerIE, getter=lambda x: f'https://tver.jp/episodes/{x}')

        if video_type != 'episodes':
            webpage = self._download_webpage(url, video_id, note='Resolving to new URL')
            video_id = self._match_id(self._search_regex(
                (r'canonical"\s*href="(https?://tver\.jp/[^"]+)"', r'&link=(https?://tver\.jp/[^?&]+)[?&]'),
                webpage, 'url regex'))

        episode_info = self._call_platform_api(
            f'v1/callEpisode/{video_id}', video_id, 'Downloading episode info', fatal=False, query={
                'require_data': 'mylist,later[epefy106ur],good[epefy106ur],resume[epefy106ur]',
            })
        episode_content = traverse_obj(
            episode_info, ('result', 'episode', 'content')) or {}

        version = traverse_obj(episode_content, ('version', {str_or_none}), default='5')
        video_info = self._download_json(
            f'https://statics.tver.jp/content/episode/{video_id}.json', video_id, 'Downloading video info',
            query={'v': version}, headers={'Referer': 'https://tver.jp/'})

        episode = strip_or_none(episode_content.get('title'))
        series = str_or_none(episode_content.get('seriesTitle'))
        title = (
            join_nonempty(series, episode, delim=' ')
            or str_or_none(video_info.get('title')))
        provider = str_or_none(episode_content.get('productionProviderName'))
        onair_label = str_or_none(episode_content.get('broadcastDateLabel'))

        thumbnails = [
            {
                'id': quality,
                'url': update_url_query(
                    f'https://statics.tver.jp/images/content/thumbnail/episode/{quality}/{video_id}.jpg',
                    {'v': version}),
                'width': width,
                'height': height,
            }
            for quality, width, height in [
                ('small', 480, 270),
                ('medium', 640, 360),
                ('large', 960, 540),
                ('xlarge', 1280, 720),
            ]
        ]

        metadata = {
            'title': title,
            'series': series,
            'episode': episode,
            # an another title which is considered "full title" for some viewers
            'alt_title': join_nonempty(title, provider, onair_label, delim=' '),
            'channel': provider,
            'thumbnails': thumbnails,
            **traverse_obj(video_info, {
                'description': ('description', {str}),
                'release_timestamp': ('viewStatus', 'startAt', {int_or_none}),
                'episode_number': ('no', {int_or_none}),
                'series_id': ('seriesID', {str}),
                'season_id': ('seasonID', {str}),
            }),
        }

        brightcove_id = traverse_obj(video_info, ('video', ('videoRefID', 'videoID'), {str}, any))
        if brightcove_id and not brightcove_id.isdecimal():
            brightcove_id = f'ref:{brightcove_id}'

        streaks_id = traverse_obj(video_info, ('streaks', 'videoRefID', {str}))
        if streaks_id and not streaks_id.startswith('ref:'):
            streaks_id = f'ref:{streaks_id}'

        # Deprecated Brightcove extraction reachable w/extractor-arg or fallback; errors are expected
        if backend == 'brightcove' or not streaks_id:
            if backend != 'brightcove':
                self.report_warning(
                    'No STREAKS ID found; falling back to Brightcove extraction', video_id=video_id)
            if not brightcove_id:
                raise ExtractorError('Unable to extract brightcove reference ID', expected=True)
            account_id = traverse_obj(video_info, (
                'video', 'accountID', {str}, {require('brightcove account ID', expected=True)}))
            return {
                **metadata,
                '_type': 'url_transparent',
                'url': smuggle_url(
                    self.BRIGHTCOVE_URL_TEMPLATE % (account_id, brightcove_id),
                    {'geo_countries': self._GEO_COUNTRIES}),
                'ie_key': 'BrightcoveNew',
            }

        project_id = video_info['streaks']['projectID']
        key_idx = dt.datetime.fromtimestamp(time_seconds(hours=9), dt.timezone.utc).month % 6 or 6

        try:
            streaks_info = self._extract_from_streaks_api(project_id, streaks_id, {
                'Origin': 'https://tver.jp',
                'Referer': 'https://tver.jp/',
                'X-Streaks-Api-Key': self._STREAKS_API_INFO[project_id]['api_key'][f'key0{key_idx}'],
            })
        except GeoRestrictedError as e:
            # Catch and re-raise with metadata_available to support --ignore-no-formats-error
            self.raise_geo_restricted(e.orig_msg, countries=self._GEO_COUNTRIES, metadata_available=True)
            streaks_info = {}

        return {
            **streaks_info,
            **metadata,
            'id': video_id,
            '_old_archive_ids': [make_archive_id('BrightcoveNew', brightcove_id)] if brightcove_id else None,
        }