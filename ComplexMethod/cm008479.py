def _real_extract(self, url):
        domain, media_type, media_id, playlist_id = self._match_valid_url(url).groups()

        if playlist_id:
            if self._yes_playlist(playlist_id, media_id):
                media_type, media_id = 'playlist', playlist_id

        if media_type == 'playlist':
            playlist = self._call_api('vod/playlist/', media_id)
            entries = []
            for video in try_get(playlist, lambda x: x['videos']['vods']) or []:
                video_id = str_or_none(video.get('id'))
                if not video_id:
                    continue
                entries.append(self.url_result(
                    f'https://{domain}/video/{video_id}',
                    self.ie_key(), video_id))
            return self.playlist_result(
                entries, media_id, playlist.get('title'),
                playlist.get('description'))

        dve_api_url = self._extract_dve_api_url(media_id, media_type)
        video_data = self._download_json(dve_api_url, media_id)
        is_live = media_type == 'live'
        if is_live:
            title = self._call_api('event/', media_id)['title']
        else:
            title = video_data['name']

        formats = []
        for proto in ('hls', 'dash'):
            media_url = video_data.get(proto + 'Url') or try_get(video_data, lambda x: x[proto]['url'])
            if not media_url:
                continue
            if proto == 'hls':
                m3u8_formats = self._extract_m3u8_formats(
                    media_url, media_id, 'mp4', live=is_live,
                    m3u8_id='hls', fatal=False, headers=self._MANIFEST_HEADERS)
                for f in m3u8_formats:
                    f.setdefault('http_headers', {}).update(self._MANIFEST_HEADERS)
                    formats.append(f)
            else:
                formats.extend(self._extract_mpd_formats(
                    media_url, media_id, mpd_id='dash', fatal=False,
                    headers=self._MANIFEST_HEADERS))

        subtitles = {}
        for subtitle in video_data.get('subtitles', []):
            subtitle_url = subtitle.get('url')
            if not subtitle_url:
                continue
            subtitles.setdefault(subtitle.get('lang', 'en_US'), []).append({
                'url': subtitle_url,
            })

        return {
            'id': media_id,
            'title': title,
            'formats': formats,
            'thumbnail': video_data.get('thumbnailUrl'),
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'tags': video_data.get('tags'),
            'is_live': is_live,
            'subtitles': subtitles,
        }