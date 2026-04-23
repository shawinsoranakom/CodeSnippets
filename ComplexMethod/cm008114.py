def _extract_from_streaks_api(self, project_id, media_id, headers=None, query=None, ssai=False, live_from_start=False):
        try:
            response = self._download_json(
                self._API_URL_TEMPLATE.format('playback', project_id, media_id, ''),
                media_id, 'Downloading STREAKS playback API JSON', headers={
                    'Accept': 'application/json',
                    'Origin': 'https://players.streaks.jp',
                    **self.geo_verification_headers(),
                    **(headers or {}),
                })
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (403, 404):
                error = self._parse_json(e.cause.response.read().decode(), media_id, fatal=False)
                message = traverse_obj(error, ('message', {str}))
                code = traverse_obj(error, ('code', {str}))
                error_id = traverse_obj(error, ('id', {int}))
                if code == 'REQUEST_FAILED':
                    if error_id == 124:
                        self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                    elif error_id == 126:
                        raise ExtractorError('Access is denied (possibly due to invalid/missing API key)')
                if code == 'MEDIA_NOT_FOUND':
                    raise ExtractorError(join_nonempty(code, message, delim=': '), expected=True)
                if code or message:
                    raise ExtractorError(join_nonempty(code, error_id, message, delim=': '))
            raise

        streaks_id = response['id']
        live_status = {
            'clip': 'was_live',
            'file': 'not_live',
            'linear': 'is_live',
            'live': 'is_live',
        }.get(response.get('type'))

        formats, subtitles = [], {}
        drm_formats = False

        for source in traverse_obj(response, ('sources', lambda _, v: v['src'])):
            if source.get('key_systems'):
                drm_formats = True
                continue

            src_url = source['src']
            is_live = live_status == 'is_live'
            ext = mimetype2ext(source.get('type'))
            if ext != 'm3u8':
                self.report_warning(f'Unsupported stream type: {ext}')
                continue

            if is_live and ssai:
                session_params = traverse_obj(self._download_json(
                    self._API_URL_TEMPLATE.format('ssai', project_id, streaks_id, '/ssai/session'),
                    media_id, 'Downloading session parameters',
                    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                    data=json.dumps({'id': source['id']}).encode(),
                ), (0, 'query', {urllib.parse.parse_qs}))
                src_url = update_url_query(src_url, session_params)

            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                src_url, media_id, 'mp4', m3u8_id='hls', fatal=False, live=is_live, query=query)
            for fmt in fmts:
                if live_from_start:
                    fmt.setdefault('downloader_options', {}).update({'ffmpeg_args': ['-live_start_index', '0']})
                    fmt['is_from_start'] = True
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if not formats and drm_formats:
            self.report_drm(media_id)
        self._remove_duplicate_formats(formats)

        for subs in traverse_obj(response, (
            'tracks', lambda _, v: v['kind'] in ('captions', 'subtitles') and url_or_none(v['src']),
        )):
            lang = traverse_obj(subs, ('srclang', {str.lower})) or 'ja'
            subtitles.setdefault(lang, []).append({'url': subs['src']})

        return {
            'id': streaks_id,
            'display_id': media_id,
            'formats': formats,
            'live_status': live_status,
            'subtitles': subtitles,
            'uploader_id': project_id,
            **traverse_obj(response, {
                'title': ('name', {str}),
                'description': ('description', {str}, filter),
                'duration': ('duration', {float_or_none}),
                'modified_timestamp': ('updated_at', {parse_iso8601}),
                'tags': ('tags', ..., {str}),
                'thumbnails': (('poster', 'thumbnail'), 'src', {'url': {url_or_none}}),
                'timestamp': ('created_at', {parse_iso8601}),
            }),
        }