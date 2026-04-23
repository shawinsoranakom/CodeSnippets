def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            response = self._download_json(
                'https://api.vid.me/videoByUrl/%s' % video_id, video_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                response = self._parse_json(e.cause.read(), video_id)
            else:
                raise

        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error), expected=True)

        video = response['video']

        if video.get('state') == 'deleted':
            raise ExtractorError(
                'Vidme said: Sorry, this video has been deleted.',
                expected=True)

        if video.get('state') in ('user-disabled', 'suspended'):
            raise ExtractorError(
                'Vidme said: This video has been suspended either due to a copyright claim, '
                'or for violating the terms of use.',
                expected=True)

        formats = []
        for f in video.get('formats', []):
            format_url = url_or_none(f.get('uri'))
            if not format_url:
                continue
            format_type = f.get('type')
            if format_type == 'dash':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
            elif format_type == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'format_id': f.get('type'),
                    'url': format_url,
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('height')),
                    'preference': 0 if f.get('type', '').endswith(
                        'clip') else 1,
                })

        if not formats and video.get('complete_url'):
            formats.append({
                'url': video.get('complete_url'),
                'width': int_or_none(video.get('width')),
                'height': int_or_none(video.get('height')),
            })

        self._sort_formats(formats)

        title = video['title']
        description = video.get('description')
        thumbnail = video.get('thumbnail_url')
        timestamp = parse_iso8601(video.get('date_created'), ' ')
        uploader = video.get('user', {}).get('username')
        uploader_id = video.get('user', {}).get('user_id')
        age_limit = 18 if video.get('nsfw') is True else 0
        duration = float_or_none(video.get('duration'))
        view_count = int_or_none(video.get('view_count'))
        like_count = int_or_none(video.get('likes_count'))
        comment_count = int_or_none(video.get('comment_count'))

        return {
            'id': video_id,
            'title': title or 'Video upload (%s)' % video_id,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'age_limit': age_limit,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'formats': formats,
        }