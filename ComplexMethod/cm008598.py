def _extract_info(self, video, video_id=None, require_title=True):
        title = video['title'] if require_title else video.get('title')

        age_limit = video.get('is_adult')
        if age_limit is not None:
            age_limit = 18 if age_limit is True else 0

        uploader_id = try_get(video, lambda x: x['author']['id'])
        category = try_get(video, lambda x: x['category']['name'])
        description = video.get('description')
        duration = int_or_none(video.get('duration'))

        return {
            'id': video.get('id') or video_id if video_id else video['id'],
            'title': title,
            'description': description,
            'thumbnail': video.get('thumbnail_url'),
            'duration': duration,
            'uploader': try_get(video, lambda x: x['author']['name']),
            'uploader_id': str(uploader_id) if uploader_id else None,
            'timestamp': unified_timestamp(video.get('created_ts')),
            'categories': [category] if category else None,
            'age_limit': age_limit,
            'view_count': int_or_none(video.get('hits')),
            'comment_count': int_or_none(video.get('comments_count')),
            'is_live': bool_or_none(video.get('is_livestream')),
            'chapters': self._extract_chapters_from_description(description, duration),
        }