def _real_extract(self, url):
        v_id = self._match_id(url)
        meta = self._download_json(self._API_BASE.format('getRecordingDrm', v_id), v_id)['response']

        thumbs = [{'id': k, 'url': v, 'http_headers': {'Accept': 'image/jpeg'}}
                  for k, v in (meta.get('images') or {}).items()]

        subs = {}
        for s in traverse_obj(meta, 'subs', 'subtitles', default=[]):
            lang = self.SUB_LANGS_MAP.get(s.get('language'), s.get('language') or 'und')
            subs.setdefault(lang, []).append({
                'url': s.get('file'),
                'ext': traverse_obj(s, 'format', expected_type=str.lower),
            })

        jwt = meta.get('jwt')
        if not jwt:
            raise ExtractorError('Site did not provide an authentication token, cannot proceed.')

        media = self._download_json(self._API_BASE.format('getMedia', v_id), v_id, query={'jwt': jwt})['response']

        formats = []
        skip_protocols = ['smil', 'f4m', 'dash']
        adaptive_url = traverse_obj(media, ('addaptiveMedia', 'hls_sec'), expected_type=url_or_none)
        if adaptive_url:
            formats = self._extract_wowza_formats(adaptive_url, v_id, skip_protocols=skip_protocols)

        adaptive_url = traverse_obj(media, ('addaptiveMedia_sl', 'hls_sec'), expected_type=url_or_none)
        if adaptive_url:
            for f in self._extract_wowza_formats(adaptive_url, v_id, skip_protocols=skip_protocols):
                formats.append({
                    **f,
                    'format_id': 'sign-' + f['format_id'],
                    'format_note': 'Sign language interpretation', 'preference': -10,
                    'language': (
                        'slv' if f.get('language') == 'eng' and f.get('acodec') != 'none'
                        else f.get('language')),
                })

        for mediafile in traverse_obj(media, ('mediaFiles', lambda _, v: url_or_none(v['streams']['https']))):
            formats.append(traverse_obj(mediafile, {
                'url': ('streams', 'https'),
                'ext': ('mediaType', {str.lower}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'tbr': ('bitrate', {int_or_none}),
                'filesize': ('filesize', {int_or_none}),
            }))

        for mediafile in traverse_obj(media, ('mediaFiles', lambda _, v: url_or_none(v['streams']['hls_sec']))):
            formats.extend(self._extract_wowza_formats(
                mediafile['streams']['hls_sec'], v_id, skip_protocols=skip_protocols))

        if any('intermission.mp4' in x['url'] for x in formats):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES, metadata_available=True)
        if any('dummy_720p.mp4' in x.get('manifest_url', '') for x in formats) and meta.get('stub') == 'error':
            raise ExtractorError(f'{self.IE_NAME} said: Clip not available', expected=True)

        return {
            'id': v_id,
            'webpage_url': ''.join(traverse_obj(meta, ('canonical', ('domain', 'path')))),
            'title': meta.get('title'),
            'formats': formats,
            'subtitles': subs,
            'thumbnails': thumbs,
            'description': meta.get('description'),
            'timestamp': unified_timestamp(traverse_obj(meta, 'broadcastDate', ('broadcastDates', 0))),
            'release_timestamp': unified_timestamp(meta.get('recordingDate')),
            'duration': meta.get('duration') or parse_duration(meta.get('length')),
            'tags': meta.get('genre'),
            'series': meta.get('showName'),
            'series_id': meta.get('showId'),
        }