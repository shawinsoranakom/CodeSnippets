def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_data = self._parse_json(self._search_regex(
            r'var\s+bridge\s*=\s*([^;]+);', webpage, 'bridged data'), video_id)
        title = video_data['title']

        formats = []
        sources = video_data.get('sources') or []
        for source in sources:
            source_src = source.get('src')
            if not source_src:
                continue
            formats.append({
                'filesize': int_or_none(source.get('kilobytes') or None, invscale=1000),
                'format_id': '-'.join(filter(None, [source.get('format'), source.get('label')])),
                'height': int_or_none(source.get('height') or None),
                'tbr': int_or_none(source.get('bitrate') or None),
                'width': int_or_none(source.get('width') or None),
                'url': source_src,
            })
        self._sort_formats(formats)

        # For both metadata and downloaded files the duration varies among
        # formats. I just pick the max one
        duration = max(filter(None, [
            float_or_none(source.get('duration'), scale=1000)
            for source in sources]))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('video', {}).get('poster'),
            'duration': duration,
            'subtitles': self._parse_subtitles(video_data, 'vttPath'),
        }