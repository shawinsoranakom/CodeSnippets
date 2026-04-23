def _real_extract(self, url):
        video_id, video_type = self._match_valid_url(url).group('id', 'type')
        video_type = self._TYPE[video_type]
        cookies = self._get_cookies(url)  # Cookies before any request
        if not cookies or not cookies.get(self._TOKEN_NAME):
            self.raise_login_required()

        video_data = traverse_obj(
            self._call_api_v1(f'{video_type}/detail', video_id, fatal=False, query={
                'tas': 5,  # See https://github.com/yt-dlp/yt-dlp/issues/7946
                'contentId': video_id,
            }), ('body', 'results', 'item', {dict})) or {}

        if video_data.get('drmProtected'):
            self.report_drm(video_id)

        geo_restricted = False
        formats, subs, has_drm = [], {}, False
        headers = {'Referer': f'{self._BASE_URL}/in'}
        content_type = traverse_obj(video_data, ('contentType', {str})) or self._CONTENT_TYPE[video_type]

        # See https://github.com/yt-dlp/yt-dlp/issues/396
        st = self._request_webpage(
            f'{self._BASE_URL}/in', video_id, 'Fetching server time').get_header('x-origin-date')
        watch = self._call_api_v2('pages/watch', video_id, content_type, cookies, st)
        player_config = traverse_obj(watch, (
            'page', 'spaces', 'player', 'widget_wrappers', lambda _, v: v['template'] == 'PlayerWidget',
            'widget', 'data', 'player_config', {dict}, any, {require('player config')}))

        for playback_set in traverse_obj(player_config, (
            ('media_asset', 'media_asset_v2'),
            ('primary', 'fallback'),
            all, lambda _, v: url_or_none(v['content_url']),
        )):
            tags = str_or_none(playback_set.get('playback_tags')) or ''
            if any(f'{prefix}:{ignore}' in tags
                   for key, prefix in self._IGNORE_MAP.items()
                   for ignore in self._configuration_arg(key)):
                continue

            tag_dict = dict((*t.split(':', 1), None)[:2] for t in tags.split(';'))
            if tag_dict.get('encryption') not in ('plain', None):
                has_drm = True
                continue

            format_url = re.sub(r'(?<=//staragvod)(\d)', r'web\1', playback_set['content_url'])
            ext = determine_ext(format_url)

            current_formats, current_subs = [], {}
            try:
                if 'package:hls' in tags or ext == 'm3u8':
                    current_formats, current_subs = self._extract_m3u8_formats_and_subtitles(
                        format_url, video_id, ext='mp4', headers=headers)
                elif 'package:dash' in tags or ext == 'mpd':
                    current_formats, current_subs = self._extract_mpd_formats_and_subtitles(
                        format_url, video_id, headers=headers)
                elif ext == 'f4m':
                    pass  # XXX: produce broken files
                else:
                    current_formats = [{
                        'url': format_url,
                        'width': int_or_none(playback_set.get('width')),
                        'height': int_or_none(playback_set.get('height')),
                    }]
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status in (403, 474):
                    geo_restricted = True
                else:
                    self.write_debug(e)
                continue

            for f in current_formats:
                for k, v in self._TAG_FIELDS.items():
                    if not f.get(k):
                        f[k] = tag_dict.get(v)
                if f.get('vcodec') != 'none' and not f.get('dynamic_range'):
                    f['dynamic_range'] = tag_dict.get('dynamic_range')
                if f.get('acodec') != 'none' and not f.get('audio_channels'):
                    f['audio_channels'] = {
                        'stereo': 2,
                        'dolby51': 6,
                    }.get(tag_dict.get('audio_channel'))
                    if (
                        'Audio_Description' in f['format_id']
                        or 'Audio Description' in (f.get('format_note') or '')
                    ):
                        f['source_preference'] = -99 + (f.get('source_preference') or -1)
                f['format_note'] = join_nonempty(
                    tag_dict.get('ladder'),
                    tag_dict.get('audio_channel') if f.get('acodec') != 'none' else None,
                    f.get('format_note'),
                    delim=', ')

            formats.extend(current_formats)
            subs = self._merge_subtitles(subs, current_subs)

        if not formats:
            if geo_restricted:
                self.raise_geo_restricted(countries=['IN'], metadata_available=True)
            elif has_drm:
                self.report_drm(video_id)
            elif not self._has_active_subscription(cookies, st):
                self.raise_no_formats('Your account does not have access to this content', expected=True)
        self._remove_duplicate_formats(formats)
        for f in formats:
            f.setdefault('http_headers', {}).update(headers)

        return {
            **self._parse_metadata_v1(video_data),
            'id': video_id,
            'formats': formats,
            'subtitles': subs,
        }