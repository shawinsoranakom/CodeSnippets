def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        blob = self._extract_data_attr(webpage, show_id, 'blob')

        show = blob['bcw_data'][show_id]

        formats = []
        for format_id, format_url in show['audio_stream'].items():
            if not url_or_none(format_url):
                continue
            for known_ext in KNOWN_EXTENSIONS:
                if known_ext in format_id:
                    ext = known_ext
                    break
            else:
                ext = None
            formats.append({
                'format_id': format_id,
                'url': format_url,
                'ext': ext,
                'vcodec': 'none',
            })
        self._sort_formats(formats)

        title = show.get('audio_title') or 'Bandcamp Weekly'
        subtitle = show.get('subtitle')
        if subtitle:
            title += ' - %s' % subtitle

        return {
            'id': show_id,
            'title': title,
            'description': show.get('desc') or show.get('short_desc'),
            'duration': float_or_none(show.get('audio_duration')),
            'is_live': False,
            'release_date': unified_strdate(show.get('published_date')),
            'series': 'Bandcamp Weekly',
            'episode': show.get('subtitle'),
            'episode_id': show_id,
            'formats': formats
        }