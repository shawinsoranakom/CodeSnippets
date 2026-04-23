def _parse_video_metadata(self, js, video_id, timestamp):
        data = self._parse_json(js, video_id, transform_source=js_to_json)
        title = unescapeHTML(data['title'])

        live_starter = try_get(data, lambda x: x['plugins']['liveStarter'], dict)
        if live_starter:
            data.update(live_starter)

        formats = []
        for tracks in data.get('tracks', {}).values():
            for video in tracks:
                video_url = video.get('src')
                if not video_url:
                    continue
                video_type = video.get('type')
                ext = determine_ext(video_url, mimetype2ext(video_type))
                if video_type == 'application/vnd.apple.mpegurl' or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                elif video_type == 'application/dash+xml' or ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        video_url, video_id, mpd_id='dash', fatal=False))
                else:
                    label = video.get('label')
                    height = self._search_regex(
                        r'^(\d+)[pP]', label or '', 'height', default=None)
                    formats.append({
                        'url': video_url,
                        'format_id': join_nonempty('http', ext, label),
                        'height': int_or_none(height),
                    })

        return {
            'id': data.get('mediaid') or video_id,
            'title': title,
            'description': data.get('description'),
            'thumbnail': data.get('image'),
            'duration': int_or_none(data.get('duration')),
            'timestamp': int_or_none(timestamp),
            'formats': formats,
        }