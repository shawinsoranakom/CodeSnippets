def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        raw_payload = self._search_regex([
            r'class="amtv-embed"[^>]+id="([0-9a-z-]+)"',
            r'id="([0-9a-z-]+)"[^>]+class="amtv-embed"',
            r'class=\\"amtv-embed\\"[^>]+id=\\"([0-9a-z-]+)\\"',
            r'id=\\"([0-9a-z-]+)\\"[^>]+class=\\"amtv-embed\\"',
            r'id=(?:\\)?"(amtve-[a-z]-\d+-[a-z]{2})',
        ], webpage, 'raw payload')
        _, stage_mode, video_id, _ = raw_payload.split('-')

        # TODO: handle s and e stage_mode (live streams and ended live streams)
        if stage_mode not in ('s', 'e'):
            video_data = self._download_json(
                'https://www.audimedia.tv/api/video/v1/videos/' + video_id,
                video_id, query={
                    'embed[]': ['video_versions', 'thumbnail_image'],
                })['results']
            formats = []

            stream_url_hls = video_data.get('stream_url_hls')
            if stream_url_hls:
                formats.extend(self._extract_m3u8_formats(
                    stream_url_hls, video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))

            stream_url_hds = video_data.get('stream_url_hds')
            if stream_url_hds:
                formats.extend(self._extract_f4m_formats(
                    stream_url_hds + '?hdcore=3.4.0',
                    video_id, f4m_id='hds', fatal=False))

            for video_version in video_data.get('video_versions', []):
                video_version_url = video_version.get('download_url') or video_version.get('stream_url')
                if not video_version_url:
                    continue
                f = {
                    'url': video_version_url,
                    'width': int_or_none(video_version.get('width')),
                    'height': int_or_none(video_version.get('height')),
                    'abr': int_or_none(video_version.get('audio_bitrate')),
                    'vbr': int_or_none(video_version.get('video_bitrate')),
                }
                bitrate = self._search_regex(r'(\d+)k', video_version_url, 'bitrate', default=None)
                if bitrate:
                    f.update({
                        'format_id': f'http-{bitrate}',
                    })
                formats.append(f)

            return {
                'id': video_id,
                'title': video_data['title'],
                'description': video_data.get('subtitle'),
                'thumbnail': video_data.get('thumbnail_image', {}).get('file'),
                'timestamp': parse_iso8601(video_data.get('publication_date')),
                'duration': int_or_none(video_data.get('duration')),
                'view_count': int_or_none(video_data.get('view_count')),
                'formats': formats,
            }