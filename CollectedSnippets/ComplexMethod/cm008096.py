def extract_format(format_id, format_url):
            f_url = url_or_none(format_url)
            if not f_url:
                return
            f = parse_resolution(format_id)
            ext = determine_ext(f_url)
            if format_id.startswith('m3u8') or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    f_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif format_id.startswith('mpd') or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    f_url, video_id, mpd_id='dash', fatal=False))
            elif ext == 'mp4' or f.get('width') or f.get('height'):
                f.update({
                    'url': f_url,
                    'format_id': format_id,
                })
                formats.append(f)