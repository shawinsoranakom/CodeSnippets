def _real_extract(self, url):
        audio_id, display_id = self._match_valid_url(url).group('id', 'slug')
        if not audio_id:
            webpage = self._download_webpage(url, display_id)
            audio_id = (
                traverse_obj(
                    get_element_html_by_class('audio-button', webpage),
                    ({extract_attributes}, ('data-audio-id', 'data-publication-id')), get_all=False)
                or self._parse_json(get_element_by_id('gtm-metadata', webpage), display_id)['pageId'])

        query = {
            'id': audio_id,
            'type': self._AUDIO_TYPE,
        }

        item = self._download_json(
            self._BASE_URL + 'audiometadata', audio_id,
            'Downloading audio JSON metadata', query=query)['items'][0]

        query['format'] = 'iis'
        urls = []
        formats = []
        for quality in self._QUALITIES:
            query['quality'] = quality
            audio_url_data = self._download_json(
                self._BASE_URL + 'getaudiourl', audio_id,
                f'Downloading {quality} format JSON metadata',
                fatal=False, query=query) or {}
            audio_url = audio_url_data.get('audioUrl')
            if not audio_url or audio_url in urls:
                continue
            urls.append(audio_url)
            ext = determine_ext(audio_url)
            coding_format = audio_url_data.get('codingFormat')
            abr = int_or_none(self._search_regex(
                r'_a(\d+)\.m4a', audio_url, 'audio bitrate',
                default=None)) or self._CODING_FORMAT_TO_ABR_MAP.get(coding_format)
            formats.append({
                'abr': abr,
                'acodec': self._EXT_TO_CODEC_MAP.get(ext),
                'ext': ext,
                'format_id': str_or_none(coding_format),
                'vcodec': 'none',
                'url': audio_url,
            })

        return {
            'id': audio_id,
            'formats': formats,
            **traverse_obj(item, {
                'title': 'subtitle',
                'series': 'title',
                'duration': ('duration', {int_or_none}),
                'thumbnail': ('displayimageurl', {url_or_none}),
                'description': 'description',
            }),
        }