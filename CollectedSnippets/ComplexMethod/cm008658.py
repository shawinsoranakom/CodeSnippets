def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        lang = mobj.group('lang') or mobj.group('lang_2')
        language_code = self._LANG_MAP.get(lang)

        config = self._download_json(f'{self._API_BASE}/config/{lang}/{video_id}', video_id, headers={
            'x-validated-age': '18',
        })

        geoblocking = traverse_obj(config, ('data', 'attributes', 'restriction', 'geoblocking')) or {}
        if geoblocking.get('restrictedArea'):
            raise GeoRestrictedError(f'Video restricted to {geoblocking["code"]!r}',
                                     countries=self._COUNTRIES_MAP.get(geoblocking['code'], ('DE', 'FR')))

        if not traverse_obj(config, ('data', 'attributes', 'rights')):
            # Eg: https://www.arte.tv/de/videos/097407-215-A/28-minuten
            # Eg: https://www.arte.tv/es/videos/104351-002-A/serviteur-du-peuple-1-23
            raise ExtractorError(
                'Video is not available in this language edition of Arte or broadcast rights expired', expected=True)

        formats, subtitles = [], {}
        secondary_formats = []
        for stream in config['data']['attributes']['streams']:
            # official player contains code like `e.get("versions")[0].eStat.ml5`
            stream_version = stream['versions'][0]
            stream_version_code = stream_version['eStat']['ml5']

            lang_pref = -1
            m = self._VERSION_CODE_RE.match(stream_version_code)
            if m:
                lang_pref = int(''.join('01'[x] for x in (
                    m.group('vlang') == language_code,      # we prefer voice in the requested language
                    not m.group('audio_desc'),              # and not the audio description version
                    bool(m.group('original_voice')),        # but if voice is not in the requested language, at least choose the original voice
                    m.group('sub_lang') == language_code,   # if subtitles are present, we prefer them in the requested language
                    not m.group('has_sub'),                 # but we prefer no subtitles otherwise
                    not m.group('sdh_sub'),                 # and we prefer not the hard-of-hearing subtitles if there are subtitles
                )))

            short_label = traverse_obj(stream_version, 'shortLabel', expected_type=str, default='?')
            if 'HLS' in stream['protocol']:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    stream['url'], video_id=video_id, ext='mp4', m3u8_id=stream_version_code, fatal=False)
                for fmt in fmts:
                    fmt.update({
                        'format_note': f'{stream_version.get("label", "unknown")} [{short_label}]',
                        'language_preference': lang_pref,
                    })
                if any(map(short_label.startswith, ('cc', 'OGsub'))):
                    secondary_formats.extend(fmts)
                else:
                    formats.extend(fmts)
                subs = self._fix_accessible_subs_locale(subs)
                self._merge_subtitles(subs, target=subtitles)

            elif stream['protocol'] in ('HTTPS', 'RTMP'):
                formats.append({
                    'format_id': f'{stream["protocol"]}-{stream_version_code}',
                    'url': stream['url'],
                    'format_note': f'{stream_version.get("label", "unknown")} [{short_label}]',
                    'language_preference': lang_pref,
                    # 'ext': 'mp4',  # XXX: may or may not be necessary, at least for HTTPS
                })

            else:
                self.report_warning(f'Skipping stream with unknown protocol {stream["protocol"]}')

        formats.extend(secondary_formats)
        self._remove_duplicate_formats(formats)

        metadata = config['data']['attributes']['metadata']

        return {
            'id': metadata['providerId'],
            'webpage_url': traverse_obj(metadata, ('link', 'url')),
            'title': traverse_obj(metadata, 'subtitle', 'title'),
            'alt_title': metadata.get('subtitle') and metadata.get('title'),
            'description': metadata.get('description'),
            'duration': traverse_obj(metadata, ('duration', 'seconds')),
            'language': metadata.get('language'),
            'timestamp': traverse_obj(config, ('data', 'attributes', 'rights', 'begin'), expected_type=parse_iso8601),
            'is_live': config['data']['attributes'].get('live', False),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': [
                {'url': image['url'], 'id': image.get('caption')}
                for image in metadata.get('images') or [] if url_or_none(image.get('url'))
            ],
            # TODO: chapters may also be in stream['segments']?
            'chapters': traverse_obj(config, ('data', 'attributes', 'chapters', 'elements', ..., {
                'start_time': 'startTime',
                'title': 'title',
            })) or None,
        }