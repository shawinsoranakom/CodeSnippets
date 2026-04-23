def extract_entry(source):
            if not isinstance(source, dict):
                return
            title = source.get('title')
            if not title:
                return
            files = source.get('files')
            if not isinstance(files, dict):
                return
            format_urls = set()
            formats = []
            for format_id in ('mobile', 'desktop'):
                format_url = try_get(
                    files, lambda x: x[format_id]['file'], compat_str)
                if not format_url or format_url in format_urls:
                    continue
                format_urls.add(format_url)
                m3u8_url = urljoin(self._LIVE_URL, format_url)
                formats.extend(self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            if not formats:
                return
            self._sort_formats(formats)
            return {
                'title': title,
                'formats': formats,
            }