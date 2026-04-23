def extract_formats(source_list):
            if not isinstance(source_list, list):
                return
            for source in source_list:
                video_url = url_or_none(source.get('file') or source.get('src'))
                if not video_url:
                    continue
                if source.get('type') == 'application/x-mpegURL' or determine_ext(video_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                    continue
                format_id = source.get('label')
                f = {
                    'url': video_url,
                    'format_id': f'{format_id}p',
                    'height': int_or_none(format_id),
                }
                if format_id:
                    # Some videos contain additional metadata (e.g.
                    # https://www.udemy.com/ios9-swift/learn/#/lecture/3383208)
                    f = add_output_format_meta(f, format_id)
                formats.append(f)