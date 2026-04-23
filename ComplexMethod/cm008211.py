def _parse_api_response(self, video, video_id, unlisted_hash=None):
        formats, subtitles = [], {}
        seen_urls = set()
        duration = traverse_obj(video, ('duration', {int_or_none}))

        for file in traverse_obj(video, (
            (('play', (None, 'progressive')), 'files', 'download'), lambda _, v: url_or_none(v['link']),
        )):
            format_url = file['link']
            if format_url in seen_urls:
                continue
            seen_urls.add(format_url)
            quality = file.get('quality')
            ext = determine_ext(format_url)
            if quality == 'hls' or ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    format_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            elif quality == 'dash' or ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    format_url, video_id, mpd_id='dash', fatal=False)
                for fmt in fmts:
                    fmt['format_id'] = join_nonempty(
                        *fmt['format_id'].split('-', 2)[:2], int_or_none(fmt.get('tbr')))
            else:
                fmt = traverse_obj(file, {
                    'ext': ('type', {mimetype2ext(default='mp4')}),
                    'vcodec': ('codec', {str.lower}),
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'filesize': ('size', {int_or_none}),
                    'fps': ('fps', {int_or_none}),
                })
                fmt.update({
                    'url': format_url,
                    'format_id': join_nonempty(
                        'http', traverse_obj(file, 'public_name', 'rendition'), quality),
                    'tbr': try_call(lambda: fmt['filesize'] * 8 / duration / 1024),
                })
                formats.append(fmt)
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if traverse_obj(video, ('metadata', 'connections', 'texttracks', 'total', {int})):
            self._merge_subtitles(self.extract_subtitles(video_id, unlisted_hash), target=subtitles)

        return {
            **traverse_obj(video, {
                'title': ('name', {str}),
                'uploader': ('user', 'name', {str}),
                'uploader_id': ('user', 'link', {url_basename}),
                'uploader_url': ('user', 'link', {url_or_none}),
                'release_timestamp': ('live', 'scheduled_start_time', {int_or_none}),
                'thumbnails': ('pictures', 'sizes', lambda _, v: url_or_none(v['link']), {
                    'url': 'link',
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                }),
            }),
            'id': video_id,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
            'live_status': {
                'streaming': 'is_live',
                'done': 'was_live',
            }.get(traverse_obj(video, ('live', 'status', {str}))),
        }