def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).groups()
        stream_data = self._call_api(
            f'https://www.vidio.com/api/livestreamings/{video_id}/detail', display_id)
        stream_meta = stream_data['livestreamings'][0]
        user = stream_data.get('users', [{}])[0]

        title = stream_meta.get('title')
        username = user.get('username')

        formats = []
        if stream_meta.get('is_drm'):
            if not self.get_param('allow_unplayable_formats'):
                self.report_drm(video_id)
        if stream_meta.get('is_premium'):
            sources = self._download_json(
                f'https://www.vidio.com/interactions_stream.json?video_id={video_id}&type=livestreamings',
                display_id, note='Downloading premier API JSON')
            if not (sources.get('source') or sources.get('source_dash')):
                self.raise_login_required('This video is only available for registered users with the appropriate subscription')

            if str_or_none(sources.get('source')):
                token_json = self._download_json(
                    f'https://www.vidio.com/live/{video_id}/tokens',
                    display_id, note='Downloading HLS token JSON', data=b'')
                formats.extend(self._extract_m3u8_formats(
                    sources['source'] + '?' + token_json.get('token', ''), display_id, 'mp4', 'm3u8_native'))
            if str_or_none(sources.get('source_dash')):
                pass
        else:
            if stream_meta.get('stream_token_url'):
                token_json = self._download_json(
                    f'https://www.vidio.com/live/{video_id}/tokens',
                    display_id, note='Downloading HLS token JSON', data=b'')
                formats.extend(self._extract_m3u8_formats(
                    stream_meta['stream_token_url'] + '?' + token_json.get('token', ''),
                    display_id, 'mp4', 'm3u8_native'))
            if stream_meta.get('stream_dash_url'):
                pass
            if stream_meta.get('stream_url'):
                formats.extend(self._extract_m3u8_formats(
                    stream_meta['stream_url'], display_id, 'mp4', 'm3u8_native'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'is_live': True,
            'description': strip_or_none(stream_meta.get('description')),
            'thumbnail': stream_meta.get('image'),
            'like_count': int_or_none(stream_meta.get('like')),
            'dislike_count': int_or_none(stream_meta.get('dislike')),
            'formats': formats,
            'uploader': user.get('name'),
            'timestamp': parse_iso8601(stream_meta.get('start_time')),
            'uploader_id': username,
            'uploader_url': format_field(username, None, 'https://www.vidio.com/@%s'),
        }