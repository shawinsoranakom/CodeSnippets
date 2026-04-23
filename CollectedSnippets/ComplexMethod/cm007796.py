def _parse_video(self, video, video_id):
        title = video['title']
        is_live = video.get('type') == 'live'
        hls_url = video.get(('streaming' if is_live else 'hls') + '_url')
        if not hls_url and video.get('geoblock' if is_live else 'geob'):
            self.raise_geo_restricted(countries=['IT'])

        if is_live:
            formats = self._extract_m3u8_formats(hls_url, video_id, 'mp4')
        else:
            formats = self._extract_akamai_formats(
                hls_url, video_id, {'http': 'videoplatform.sky.it'})
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'formats': formats,
            'thumbnail': dict_get(video, ('video_still', 'video_still_medium', 'thumb')),
            'description': video.get('short_desc') or None,
            'timestamp': unified_timestamp(video.get('create_date')),
            'duration': int_or_none(video.get('duration_sec')) or parse_duration(video.get('duration')),
            'is_live': is_live,
        }