def _real_extract(self, url):
        video_id, title, key = self._match_valid_url(url).group('id', 'title', 'key')
        settings = self._call_api(video_id, title, key)

        restriction = settings.get('restrictionReason')
        if restriction == 'RegionRestricted':
            self.raise_geo_restricted()
        if restriction and restriction != 'None':
            raise ExtractorError(
                f'{self.IE_NAME} said: {restriction}', expected=True)

        formats, parsed_urls = [], {None}
        for rendition_id, rendition in settings['renditions'].items():
            audio, version, extra = rendition_id.split('_')
            m3u8_url = url_or_none(try_get(rendition, lambda x: x['bitrates']['hls']))
            if m3u8_url not in parsed_urls:
                parsed_urls.add(m3u8_url)
                frmt = self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id=rendition_id, fatal=False)
                for f in frmt:
                    f['language'] = audio
                    f['format_note'] = f'{version}, {extra}'
                formats.extend(frmt)

        subtitles = {}
        for rendition_id, rendition in settings['renditions'].items():
            audio, version, extra = rendition_id.split('_')
            for cc_file in rendition.get('ccFiles') or []:
                cc_url = url_or_none(try_get(cc_file, lambda x: x[2]))
                cc_lang = try_get(cc_file, (lambda x: x[1].replace(' ', '-').lower(), lambda x: x[0]), str)
                if cc_url not in parsed_urls and cc_lang:
                    parsed_urls.add(cc_url)
                    subtitles.setdefault(cc_lang, []).append({'url': cc_url})

        return {
            'id': video_id,
            'title': video_id,
            'subtitles': subtitles,
            'formats': formats,
            'series': title,
            'season_number': int_or_none(
                self._search_regex(r's(\d+)', key, 'season number', default=None)),
            'episode_number': int_or_none(
                self._search_regex(r'e(\d+)', key, 'episode number', default=None)),
            'http_headers': {'Referer': url},
        }