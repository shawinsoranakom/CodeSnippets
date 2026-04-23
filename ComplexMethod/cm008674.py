def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._download_json(
            'https://rumble.com/embedJS/u3/', video_id,
            query={'request': 'video', 'ver': 2, 'v': video_id})

        sys_msg = traverse_obj(video, ('sys', 'msg'))
        if sys_msg:
            self.report_warning(sys_msg, video_id=video_id)

        if video.get('live') == 0:
            live_status = 'not_live' if video.get('livestream_has_dvr') is None else 'was_live'
        elif video.get('live') == 1:
            live_status = 'is_upcoming' if video.get('livestream_has_dvr') else 'was_live'
        elif video.get('live') == 2:
            live_status = 'is_live'
        else:
            live_status = None

        formats = []
        for format_type, format_info in (video.get('ua') or {}).items():
            if isinstance(format_info, dict):
                for height, video_info in format_info.items():
                    if not traverse_obj(video_info, ('meta', 'h', {int_or_none})):
                        video_info.setdefault('meta', {})['h'] = height
                format_info = format_info.values()

            for video_info in format_info:
                meta = video_info.get('meta') or {}
                if not video_info.get('url'):
                    continue
                # With default query params returns m3u8 variants which are duplicates, without returns tar files
                if format_type == 'tar':
                    continue
                if format_type == 'hls':
                    if meta.get('live') is True and video.get('live') == 1:
                        live_status = 'post_live'
                    formats.extend(self._extract_m3u8_formats(
                        video_info['url'], video_id,
                        ext='mp4', m3u8_id='hls', fatal=False, live=live_status == 'is_live'))
                    continue
                is_timeline = format_type == 'timeline'
                is_audio = format_type == 'audio'
                formats.append({
                    'acodec': 'none' if is_timeline else None,
                    'vcodec': 'none' if is_audio else None,
                    'url': video_info['url'],
                    'format_id': join_nonempty(format_type, format_field(meta, 'h', '%sp')),
                    'format_note': 'Timeline' if is_timeline else None,
                    'fps': None if is_timeline or is_audio else video.get('fps'),
                    **traverse_obj(meta, {
                        'tbr': ('bitrate', {int_or_none}),
                        'filesize': ('size', {int_or_none}),
                        'width': ('w', {int_or_none}),
                        'height': ('h', {int_or_none}),
                    }),
                })

        subtitles = {
            lang: [{
                'url': sub_info['path'],
                'name': sub_info.get('language') or '',
            }] for lang, sub_info in (video.get('cc') or {}).items() if sub_info.get('path')
        }

        author = video.get('author') or {}
        thumbnails = traverse_obj(video, ('t', ..., {'url': 'i', 'width': 'w', 'height': 'h'}))
        if not thumbnails and video.get('i'):
            thumbnails = [{'url': video['i']}]

        if live_status in {'is_live', 'post_live'}:
            duration = None
        else:
            duration = int_or_none(video.get('duration'))

        return {
            'id': video_id,
            'title': unescapeHTML(video.get('title')),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'timestamp': parse_iso8601(video.get('pubDate')),
            'channel': author.get('name'),
            'channel_url': author.get('url'),
            'duration': duration,
            'uploader': author.get('name'),
            'live_status': live_status,
        }