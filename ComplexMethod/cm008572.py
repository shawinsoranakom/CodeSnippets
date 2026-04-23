def _extract_formats_and_subtitles(self, video_id, content_media_json):
        urls = []
        formats = []
        subtitles = {}
        for video in traverse_obj(content_media_json, ('renditions', ..., {dict})):
            video_url = video.get('url')
            format_id = video.get('type')
            if not video_url or format_id == 'thumbs' or video_url in urls:
                continue
            urls.append(video_url)
            ext = mimetype2ext(video.get('mimetype')) or determine_ext(video_url)
            if ext == 'm3u8':
                m3u8_fmts, m3u8_subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id or 'hls', fatal=False)
                formats.extend(m3u8_fmts)
                self._merge_subtitles(m3u8_subs, target=subtitles)
            elif ext == 'mpd':
                continue  # all mpd urls give 404 errors
            else:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'vcodec': video.get('videoencoding') or video.get('video_codec'),
                    'width': int_or_none(video.get('width')),
                    'height': int_or_none(video.get('height')),
                    'filesize': traverse_obj(video, (
                        ('file_size', 'fileSize'), (None, ('value')), {int_or_none}), get_all=False),
                    'tbr': int_or_none(video.get('bitrate'), 1000) or None,
                    'ext': ext,
                })

        return formats, subtitles