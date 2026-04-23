def _extract_video(self, info, display_id):
        video_id = compat_str(info['id'])
        title = info['title']

        paths = []
        for manifest_url in (info.get('manifest') or {}).values():
            if not manifest_url:
                continue
            manifest_url = update_url_query(manifest_url, {'filter': ''})
            path = self._search_regex(r'https?://[^/]+/(.+?)\.ism/', manifest_url, 'path')
            if path in paths:
                continue
            paths.append(path)

            def url_repl(proto, suffix):
                return re.sub(
                    r'(?:hls|dash|hss)([.-])', proto + r'\1', re.sub(
                        r'\.ism/(?:[^.]*\.(?:m3u8|mpd)|[Mm]anifest)',
                        '.ism/' + suffix, manifest_url))

            def make_urls(proto, suffix):
                urls = [url_repl(proto, suffix)]
                hd_url = urls[0].replace('/manifest/', '/ngvod/')
                if hd_url != urls[0]:
                    urls.append(hd_url)
                return urls

            for man_url in make_urls('dash', '.mpd'):
                formats = self._extract_mpd_formats(
                    man_url, video_id, mpd_id='dash', fatal=False)
            for man_url in make_urls('hss', 'Manifest'):
                formats.extend(self._extract_ism_formats(
                    man_url, video_id, ism_id='mss', fatal=False))
            for man_url in make_urls('hls', '.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    man_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls',
                    fatal=False))
            if formats:
                break
        else:
            if info.get('isDrm'):
                raise ExtractorError(
                    'Video %s is DRM protected' % video_id, expected=True)
            if info.get('geoblocked'):
                raise self.raise_geo_restricted()
            if not info.get('free', True):
                raise ExtractorError(
                    'Video %s is not available for free' % video_id, expected=True)
        self._sort_formats(formats)

        description = info.get('articleLong') or info.get('articleShort')
        timestamp = parse_iso8601(info.get('broadcastStartDate'), ' ')
        duration = parse_duration(info.get('duration'))

        f = info.get('format', {})

        thumbnails = [{
            'url': 'https://aistvnow-a.akamaihd.net/tvnow/movie/%s' % video_id,
        }]
        thumbnail = f.get('defaultImage169Format') or f.get('defaultImage169Logo')
        if thumbnail:
            thumbnails.append({
                'url': thumbnail,
            })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'series': f.get('title'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
            'episode': title,
            'formats': formats,
        }