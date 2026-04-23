def _real_extract(self, url):
        display_id, video_id = re.match(self._VALID_URL, url).groups()

        try:
            episode = self._download_json(
                self._API_BASE + 'client/v1/player/episode/' + video_id, video_id)
        except ExtractorError as e:
            self._handle_error(e, 403)

        title = episode['titulo']

        formats = []
        for source in episode.get('sources', []):
            src = source.get('src')
            if not src:
                continue
            src_type = source.get('type')
            if src_type == 'application/vnd.apple.mpegurl':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif src_type == 'application/dash+xml':
                formats.extend(self._extract_mpd_formats(
                    src, video_id, mpd_id='dash', fatal=False))
        self._sort_formats(formats)

        heartbeat = episode.get('heartbeat') or {}
        omniture = episode.get('omniture') or {}
        get_meta = lambda x: heartbeat.get(x) or omniture.get(x)

        return {
            'display_id': display_id,
            'id': video_id,
            'title': title,
            'description': episode.get('descripcion'),
            'thumbnail': episode.get('imgPoster'),
            'duration': int_or_none(episode.get('duration')),
            'formats': formats,
            'channel': get_meta('channel'),
            'season': get_meta('season'),
            'episode_number': int_or_none(get_meta('episodeNumber')),
        }