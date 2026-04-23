def _extract_yahoo_video(self, video_id, country):
        video = self._download_json(
            'https://%s.yahoo.com/_td/api/resource/VideoService.videos;view=full;video_ids=["%s"]' % (country, video_id),
            video_id, 'Downloading video JSON metadata')[0]
        title = video['title']

        if country == 'malaysia':
            country = 'my'

        is_live = video.get('live_state') == 'live'
        fmts = ('m3u8',) if is_live else ('webm', 'mp4')

        urls = []
        formats = []
        subtitles = {}
        for fmt in fmts:
            media_obj = self._download_json(
                'https://video-api.yql.yahoo.com/v1/video/sapi/streams/' + video_id,
                video_id, 'Downloading %s JSON metadata' % fmt,
                headers=self.geo_verification_headers(), query={
                    'format': fmt,
                    'region': country.upper(),
                })['query']['results']['mediaObj'][0]
            msg = media_obj.get('status', {}).get('msg')

            for s in media_obj.get('streams', []):
                host = s.get('host')
                path = s.get('path')
                if not host or not path:
                    continue
                s_url = host + path
                if s.get('format') == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        s_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                    continue
                tbr = int_or_none(s.get('bitrate'))
                formats.append({
                    'url': s_url,
                    'format_id': fmt + ('-%d' % tbr if tbr else ''),
                    'width': int_or_none(s.get('width')),
                    'height': int_or_none(s.get('height')),
                    'tbr': tbr,
                    'fps': int_or_none(s.get('framerate')),
                })

            for cc in media_obj.get('closedcaptions', []):
                cc_url = cc.get('url')
                if not cc_url or cc_url in urls:
                    continue
                urls.append(cc_url)
                subtitles.setdefault(cc.get('lang') or 'en-US', []).append({
                    'url': cc_url,
                    'ext': mimetype2ext(cc.get('content_type')),
                })

        streaming_url = video.get('streaming_url')
        if streaming_url and not is_live:
            formats.extend(self._extract_m3u8_formats(
                streaming_url, video_id, 'mp4',
                'm3u8_native', m3u8_id='hls', fatal=False))

        if not formats and msg == 'geo restricted':
            self.raise_geo_restricted()

        self._sort_formats(formats)

        thumbnails = []
        for thumb in video.get('thumbnails', []):
            thumb_url = thumb.get('url')
            if not thumb_url:
                continue
            thumbnails.append({
                'id': thumb.get('tag'),
                'url': thumb.get('url'),
                'width': int_or_none(thumb.get('width')),
                'height': int_or_none(thumb.get('height')),
            })

        series_info = video.get('series_info') or {}

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': clean_html(video.get('description')),
            'timestamp': parse_iso8601(video.get('publish_time')),
            'subtitles': subtitles,
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('view_count')),
            'is_live': is_live,
            'series': video.get('show_name'),
            'season_number': int_or_none(series_info.get('season_number')),
            'episode_number': int_or_none(series_info.get('episode_number')),
        }