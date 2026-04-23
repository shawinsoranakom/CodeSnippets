def _real_extract(self, url):
        content_id = self._match_id(url)

        content_info = self._download_json(
            self._API_BASE_URL + self._API_URL_QUERY % content_id,
            content_id, note='Downloading JSON metadata')

        title = content_info['Title']
        thumbnail = content_info.get('Logo')
        location = content_info.get('Location')
        streams_url = content_info.get('StreamUrl')
        if not streams_url:
            raise ExtractorError('No downloadable streams found', expected=True)
        if not streams_url.startswith('http://'):
            streams_url = compat_urlparse.urljoin(url, streams_url)

        streams = self._download_json(
            streams_url, content_id, note='Downloading stream data',
            transform_source=lambda s: re.sub(r'^\s*\((.*)\);\s*$', r'\1', s))['Streams']

        is_live = None
        formats = []
        for stream in streams:
            if stream.get('Type') == 'Live':
                is_live = True
            reliability = stream.get('Reliability')
            format_note = (
                'Reliability: %d%%' % reliability
                if reliability is not None else None)
            formats.append({
                'preference': (
                    0 if reliability is None or reliability > 90
                    else 1),
                'abr': stream.get('Bandwidth'),
                'ext': stream.get('MediaType').lower(),
                'acodec': stream.get('MediaType'),
                'vcodec': 'none',
                'url': stream.get('Url'),
                'source_preference': reliability,
                'format_note': format_note,
            })
        self._sort_formats(formats)

        return {
            'id': content_id,
            'title': self._live_title(title) if is_live else title,
            'formats': formats,
            'thumbnail': thumbnail,
            'location': location,
            'is_live': is_live,
        }