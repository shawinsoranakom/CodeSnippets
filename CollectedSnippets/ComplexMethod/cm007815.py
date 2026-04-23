def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        lang = mobj.group('lang') or mobj.group('lang_2')

        info = self._download_json(
            '%s/config/%s/%s' % (self._API_BASE, lang, video_id), video_id)
        player_info = info['videoJsonPlayer']

        vsr = try_get(player_info, lambda x: x['VSR'], dict)
        if not vsr:
            error = None
            if try_get(player_info, lambda x: x['custom_msg']['type']) == 'error':
                error = try_get(
                    player_info, lambda x: x['custom_msg']['msg'], compat_str)
            if not error:
                error = 'Video %s is not available' % player_info.get('VID') or video_id
            raise ExtractorError(error, expected=True)

        upload_date_str = player_info.get('shootingDate')
        if not upload_date_str:
            upload_date_str = (player_info.get('VRA') or player_info.get('VDA') or '').split(' ')[0]

        title = (player_info.get('VTI') or player_info['VID']).strip()
        subtitle = player_info.get('VSU', '').strip()
        if subtitle:
            title += ' - %s' % subtitle

        qfunc = qualities(['MQ', 'HQ', 'EQ', 'SQ'])

        LANGS = {
            'fr': 'F',
            'de': 'A',
            'en': 'E[ANG]',
            'es': 'E[ESP]',
            'it': 'E[ITA]',
            'pl': 'E[POL]',
        }

        langcode = LANGS.get(lang, lang)

        formats = []
        for format_id, format_dict in vsr.items():
            f = dict(format_dict)
            format_url = url_or_none(f.get('url'))
            streamer = f.get('streamer')
            if not format_url and not streamer:
                continue
            versionCode = f.get('versionCode')
            l = re.escape(langcode)

            # Language preference from most to least priority
            # Reference: section 6.8 of
            # https://www.arte.tv/sites/en/corporate/files/complete-technical-guidelines-arte-geie-v1-07-1.pdf
            PREFERENCES = (
                # original version in requested language, without subtitles
                r'VO{0}$'.format(l),
                # original version in requested language, with partial subtitles in requested language
                r'VO{0}-ST{0}$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO{0}-STM{0}$'.format(l),
                # non-original (dubbed) version in requested language, without subtitles
                r'V{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles partial subtitles in requested language
                r'V{0}-ST{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'V{0}-STM{0}$'.format(l),
                # original version in requested language, with partial subtitles in different language
                r'VO{0}-ST(?!{0}).+?$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO{0}-STM(?!{0}).+?$'.format(l),
                # original version in different language, with partial subtitles in requested language
                r'VO(?:(?!{0}).+?)?-ST{0}$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO(?:(?!{0}).+?)?-STM{0}$'.format(l),
                # original version in different language, without subtitles
                r'VO(?:(?!{0}))?$'.format(l),
                # original version in different language, with partial subtitles in different language
                r'VO(?:(?!{0}).+?)?-ST(?!{0}).+?$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO(?:(?!{0}).+?)?-STM(?!{0}).+?$'.format(l),
            )

            for pref, p in enumerate(PREFERENCES):
                if re.match(p, versionCode):
                    lang_pref = len(PREFERENCES) - pref
                    break
            else:
                lang_pref = -1

            media_type = f.get('mediaType')
            if media_type == 'hls':
                m3u8_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=format_id, fatal=False)
                for m3u8_format in m3u8_formats:
                    m3u8_format['language_preference'] = lang_pref
                formats.extend(m3u8_formats)
                continue

            format = {
                'format_id': format_id,
                'preference': -10 if f.get('videoFormat') == 'M3U8' else None,
                'language_preference': lang_pref,
                'format_note': '%s, %s' % (f.get('versionCode'), f.get('versionLibelle')),
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'tbr': int_or_none(f.get('bitrate')),
                'quality': qfunc(f.get('quality')),
            }

            if media_type == 'rtmp':
                format['url'] = f['streamer']
                format['play_path'] = 'mp4:' + f['url']
                format['ext'] = 'flv'
            else:
                format['url'] = f['url']

            formats.append(format)

        self._sort_formats(formats)

        return {
            'id': player_info.get('VID') or video_id,
            'title': title,
            'description': player_info.get('VDE'),
            'upload_date': unified_strdate(upload_date_str),
            'thumbnail': player_info.get('programImage') or player_info.get('VTU', {}).get('IUR'),
            'formats': formats,
        }