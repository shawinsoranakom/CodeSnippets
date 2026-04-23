def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            config = self._download_json(
                url.replace('://playout.3qsdn.com/', '://playout.3qsdn.com/config/'), video_id)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                self.raise_geo_restricted()
            raise

        live = config.get('streamContent') == 'live'
        aspect = float_or_none(config.get('aspect'))

        formats = []
        subtitles = {}
        for source_type, source in (config.get('sources') or {}).items():
            if not source:
                continue
            if source_type == 'dash':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    source, video_id, mpd_id='mpd', fatal=False)
                formats.extend(fmts)
                subtitles = self._merge_subtitles(subtitles, subs)
            elif source_type == 'hls':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    source, video_id, 'mp4', live=live, m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                subtitles = self._merge_subtitles(subtitles, subs)
            elif source_type == 'progressive':
                for s in source:
                    src = s.get('src')
                    if not (src and self._is_valid_url(src, video_id)):
                        continue
                    ext = determine_ext(src)
                    height = int_or_none(s.get('height'))
                    formats.append({
                        'ext': ext,
                        'format_id': join_nonempty('http', ext, height and f'{height}p'),
                        'height': height,
                        'source_preference': 0,
                        'url': src,
                        'vcodec': 'none' if height == 0 else None,
                        'width': int(height * aspect) if height and aspect else None,
                    })

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
            'title': title,
            'thumbnail': config.get('poster') or None,
            'description': config.get('description') or None,
            'timestamp': parse_iso8601(config.get('upload_date')),
            'duration': float_or_none(config.get('vlength')) or None,
            'is_live': live,
            'formats': formats,
            'subtitles': subtitles,
            # It seems like this would be correctly handled by default
            # However, unless someone can confirm this, the old
            # behaviour is being kept as-is
            '_format_sort_fields': ('res', 'source_preference'),
        }