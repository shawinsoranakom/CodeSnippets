def _extract_yahoo_video(self, video_id, country):
        video = self._download_json(
            f'https://video-api.yql.yahoo.com/v1/video/sapi/streams/{video_id}',
            video_id, 'Downloading video JSON metadata')['query']['results']['mediaObj'][0]['meta']
        if country == 'malaysia':
            country = 'my'

        is_live = traverse_obj(video, ('uplynk_live', {bool})) is True
        fmts = ('m3u8',) if is_live else ('webm', 'mp4')

        urls = []
        formats = []
        subtitles = {}
        for fmt in fmts:
            media_obj = self._download_json(
                'https://video-api.yql.yahoo.com/v1/video/sapi/streams/' + video_id,
                video_id, f'Downloading {fmt} JSON metadata',
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
                    'format_id': join_nonempty(fmt, tbr),
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

        if not formats and msg == 'geo restricted':
            self.raise_geo_restricted(metadata_available=True)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **traverse_obj(video, {
                'title': ('title', {clean_html}),
                'description': ('description', {clean_html}),
                'thumbnail': ('thumbnail', {url_or_none}, {update_url(scheme='https')}),
                'timestamp': ('publish_time', {parse_iso8601}),
                'duration': ('duration', {int_or_none}),
                'view_count': ('view_count', {int_or_none}),
                'series': ('show_name', {str}, filter),
            }),
        }