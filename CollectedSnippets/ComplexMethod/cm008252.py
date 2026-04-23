def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_data = self._search_json(
            r'var\s+bridge\s*=', webpage, 'bridged data', video_id)

        formats = []
        for source in traverse_obj(video_data, (
            'sources', lambda _, v: v['format'] != 'playlist' and url_or_none(v['src']),
        )):
            source_url = self._proto_relative_url(source['src'])
            if determine_ext(source_url) == 'm3u8':
                fmts = self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            else:
                fmts = [{'url': source_url}]

            for fmt in fmts:
                fmt.update(traverse_obj(source, {
                    'duration': ('duration', {float_or_none(scale=1000)}),
                    'filesize': ('kilobytes', {float_or_none(invscale=1000)}),
                    'format_id': (('format', 'label'), {str}, all, {lambda x: join_nonempty(*x)}),
                    'height': ('height', {int_or_none}),
                    'tbr': ('bitrate', {int_or_none}),
                    'width': ('width', {int_or_none}),
                }))
            formats.extend(fmts)

        subtitles = {}
        for translation in traverse_obj(video_data, (
            'translations', lambda _, v: url_or_none(v['vttPath']),
        )):
            lang = translation.get('language_w3c') or ISO639Utils.long2short(translation.get('language_medium')) or 'und'
            subtitles.setdefault(lang, []).append({
                'ext': 'vtt',
                'url': self._proto_relative_url(translation['vttPath']),
            })

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video_data, {
                'title': ('title', {clean_html}),
                'description': ('description', {clean_html}, filter),
                'thumbnail': ('video', 'poster', {self._proto_relative_url}, {url_or_none}),
            }),
        }