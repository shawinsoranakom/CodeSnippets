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
                    files, lambda x: x[format_id]['file'], str)
                if not format_url or format_url in format_urls:
                    continue
                format_urls.add(format_url)
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            if not formats and not self.get_param('ignore_no_formats'):
                return
            return {
                'title': title,
                'formats': formats,
                'thumbnail': files.get('thumbnail'),
            }