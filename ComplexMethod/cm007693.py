def _real_extract(self, url):
        display_id = self._match_id(url)
        media_info = self._download_json('http://m.trilulilu.ro/%s?format=json' % display_id, display_id)

        age_limit = 0
        errors = media_info.get('errors', {})
        if errors.get('friends'):
            raise ExtractorError('This video is private.', expected=True)
        elif errors.get('geoblock'):
            raise ExtractorError('This video is not available in your country.', expected=True)
        elif errors.get('xxx_unlogged'):
            age_limit = 18

        media_class = media_info.get('class')
        if media_class not in ('video', 'audio'):
            raise ExtractorError('not a video or an audio')

        user = media_info.get('user', {})

        thumbnail = media_info.get('cover_url')
        if thumbnail:
            thumbnail.format(width='1600', height='1200')

        # TODO: get correct ext for audio files
        stream_type = media_info.get('stream_type')
        formats = [{
            'url': media_info['href'],
            'ext': stream_type,
        }]
        if media_info.get('is_hd'):
            formats.append({
                'format_id': 'hd',
                'url': media_info['hrefhd'],
                'ext': stream_type,
            })
        if media_class == 'audio':
            formats[0]['vcodec'] = 'none'
        else:
            formats[0]['format_id'] = 'sd'

        return {
            'id': media_info['identifier'].split('|')[1],
            'display_id': display_id,
            'formats': formats,
            'title': media_info['title'],
            'description': media_info.get('description'),
            'thumbnail': thumbnail,
            'uploader_id': user.get('username'),
            'uploader': user.get('fullname'),
            'timestamp': parse_iso8601(media_info.get('published'), ' '),
            'duration': int_or_none(media_info.get('duration')),
            'view_count': int_or_none(media_info.get('count_views')),
            'like_count': int_or_none(media_info.get('count_likes')),
            'comment_count': int_or_none(media_info.get('count_comments')),
            'age_limit': age_limit,
        }