def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            config = self._download_json(
                url.replace('://playout.3qsdn.com/', '://playout.3qsdn.com/config/'), video_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                self.raise_geo_restricted()
            raise

        live = config.get('streamContent') == 'live'
        aspect = float_or_none(config.get('aspect'))

        formats = []
        for source_type, source in (config.get('sources') or {}).items():
            if not source:
                continue
            if source_type == 'dash':
                formats.extend(self._extract_mpd_formats(
                    source, video_id, mpd_id='mpd', fatal=False))
            elif source_type == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    source, video_id, 'mp4', 'm3u8' if live else 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif source_type == 'progressive':
                for s in source:
                    src = s.get('src')
                    if not (src and self._is_valid_url(src, video_id)):
                        continue
                    width = None
                    format_id = ['http']
                    ext = determine_ext(src)
                    if ext:
                        format_id.append(ext)
                    height = int_or_none(s.get('height'))
                    if height:
                        format_id.append('%dp' % height)
                        if aspect:
                            width = int(height * aspect)
                    formats.append({
                        'ext': ext,
                        'format_id': '-'.join(format_id),
                        'height': height,
                        'source_preference': 0,
                        'url': src,
                        'vcodec': 'none' if height == 0 else None,
                        'width': width,
                    })
        for f in formats:
            if f.get('acodec') == 'none':
                f['preference'] = -40
            elif f.get('vcodec') == 'none':
                f['preference'] = -50
        self._sort_formats(formats, ('preference', 'width', 'height', 'source_preference', 'tbr', 'vbr', 'abr', 'ext', 'format_id'))

        subtitles = {}
        for subtitle in (config.get('subtitles') or []):
            src = subtitle.get('src')
            if not src:
                continue
            subtitles.setdefault(subtitle.get('label') or 'eng', []).append({
                'url': src,
            })

        title = config.get('title') or video_id

        return {
            'id': video_id,
            'title': self._live_title(title) if live else title,
            'thumbnail': config.get('poster') or None,
            'description': config.get('description') or None,
            'timestamp': parse_iso8601(config.get('upload_date')),
            'duration': float_or_none(config.get('vlength')) or None,
            'is_live': live,
            'formats': formats,
            'subtitles': subtitles,
        }