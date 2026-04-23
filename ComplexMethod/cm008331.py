def _real_extract(self, url):
        display_id = self._match_id(url)
        query = {'embedded': 'false', 'mcV6': 'true'}
        headers = {}

        if self._get_cookies(self._TOKEN_URL).get('ams'):
            token = self._download_json(
                self._TOKEN_URL, display_id, 'Fetching token for age verification',
                'Unable to fetch age verification token', fatal=False)
            id_token = traverse_obj(token, ('idToken', {str}))
            decoded_token = traverse_obj(id_token, ({jwt_decode_hs256}, {dict}))
            user_id = traverse_obj(decoded_token, (('user_id', 'sub'), {str}), get_all=False)
            if not user_id:
                self.report_warning('Unable to extract token, continuing without authentication')
            else:
                headers['x-authorization'] = f'Bearer {id_token}'
                query['userId'] = user_id
                if decoded_token.get('age_rating') != 18:
                    self.report_warning('Account is not verified as 18+; video may be unavailable')

        page_data = self._download_json(
            f'https://api.ardmediathek.de/page-gateway/pages/ard/item/{display_id}',
            display_id, query=query, headers=headers)

        # For user convenience we use the old contentId instead of the longer crid
        # Ref: https://github.com/yt-dlp/yt-dlp/issues/8731#issuecomment-1874398283
        old_id = traverse_obj(page_data, ('tracking', 'atiCustomVars', 'contentId', {int}))
        if old_id is not None:
            video_id = str(old_id)
            archive_ids = [make_archive_id(ARDBetaMediathekIE, display_id)]
        else:
            self.report_warning(f'Could not extract contentId{bug_reports_message()}')
            video_id = display_id
            archive_ids = None

        player_data = traverse_obj(
            page_data, ('widgets', lambda _, v: v['type'] in ('player_ondemand', 'player_live'), {dict}), get_all=False)
        is_live = player_data.get('type') == 'player_live'
        media_data = traverse_obj(player_data, ('mediaCollection', 'embedded', {dict}))

        if player_data.get('blockedByFsk'):
            self.raise_login_required('This video is only available for age verified users or after 22:00')

        formats = []
        subtitles = {}
        for stream in traverse_obj(media_data, ('streams', ..., {dict})):
            kind = stream.get('kind')
            # Prioritize main stream over sign language and others
            preference = 1 if kind == 'main' else None
            for media in traverse_obj(stream, ('media', lambda _, v: url_or_none(v['url']))):
                media_url = media['url']

                audio_kind = traverse_obj(media, (
                    'audios', 0, 'kind', {str}), default='').replace('standard', '')
                lang_code = traverse_obj(media, ('audios', 0, 'languageCode', {str})) or 'deu'
                lang = join_nonempty(lang_code, audio_kind)
                language_preference = 10 if lang == 'deu' else -10

                if determine_ext(media_url) == 'm3u8':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        media_url, video_id, m3u8_id=f'hls-{kind}', preference=preference, fatal=False, live=is_live)
                    for f in fmts:
                        f['language'] = lang
                        f['language_preference'] = language_preference
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                else:
                    formats.append({
                        'url': media_url,
                        'format_id': f'http-{kind}',
                        'preference': preference,
                        'language': lang,
                        'language_preference': language_preference,
                        **traverse_obj(media, {
                            'format_note': ('forcedLabel', {str}),
                            'width': ('maxHResolutionPx', {int_or_none}),
                            'height': ('maxVResolutionPx', {int_or_none}),
                            'vcodec': ('videoCodec', {str}),
                        }),
                    })

        for sub in traverse_obj(media_data, ('subtitles', ..., {dict})):
            for sources in traverse_obj(sub, ('sources', lambda _, v: url_or_none(v['url']))):
                subtitles.setdefault(sub.get('languageCode') or 'deu', []).append({
                    'url': sources['url'],
                    'ext': {'webvtt': 'vtt', 'ebutt': 'ttml'}.get(sources.get('kind')),
                })

        age_limit = traverse_obj(page_data, ('fskRating', {lambda x: remove_start(x, 'FSK')}, {int_or_none}))
        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            'age_limit': age_limit,
            **traverse_obj(media_data, {
                'chapters': ('pluginData', 'jumpmarks@all', 'chapterArray', lambda _, v: int_or_none(v['chapterTime']), {
                    'start_time': ('chapterTime', {int_or_none}),
                    'title': ('chapterTitle', {str}),
                }),
            }),
            **traverse_obj(media_data, ('meta', {
                'title': 'title',
                'description': 'synopsis',
                'timestamp': ('broadcastedOnDateTime', {parse_iso8601}),
                'series': 'seriesTitle',
                'thumbnail': ('images', 0, 'url', {url_or_none}),
                'duration': ('durationSeconds', {int_or_none}),
                'channel': 'clipSourceName',
            })),
            **self._extract_episode_info(page_data.get('title')),
            '_old_archive_ids': archive_ids,
        }