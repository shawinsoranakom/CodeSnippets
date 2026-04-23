def _extract_entry(self, data, url, video_id=None):
        video_id = str(video_id or data['nid'])
        title = data['title']

        formats = self._extract_m3u8_formats(
            data['file'], video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        description = data.get('description')
        thumbnail = urljoin(url, data.get('image'))
        series = data.get('show_name')
        episode = data.get('episode_name')

        subtitles = {}
        tracks = data.get('tracks')
        if isinstance(tracks, list):
            for track in tracks:
                if not isinstance(track, dict):
                    continue
                if track.get('kind') != 'captions':
                    continue
                track_file = url_or_none(track.get('file'))
                if not track_file:
                    continue
                label = track.get('label')
                lang = self._SUBTITLE_LANGS.get(label, label) or 'en'
                subtitles.setdefault(lang, []).append({
                    'url': track_file,
                })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'series': series,
            'episode': episode,
            'formats': formats,
            'subtitles': subtitles,
        }