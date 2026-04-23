def _extract_video_info(self, data):
        thumbnails = []
        for image in traverse_obj(data, ('included', 'images')):
            if image.get('type') not in ('episode_image', 'bonus_feature_image'):
                continue
            thumbnails.extend([{
                'id': name,
                'url': url,
            } for name, url in (image.get('attributes') or {}).items() if url_or_none(url)])

        attributes = data.get('attributes') or {}
        title = traverse_obj(attributes, 'title', 'display_title')
        sub_only = attributes.get('is_sponsors_only')

        episode_id = str_or_none(data.get('uuid'))
        video_id = str_or_none(data.get('id'))
        if video_id and 'parent_content_id' in attributes:  # parent_content_id is a bonus-only key
            video_id += '-bonus'  # there are collisions with bonus ids and regular ids
        elif not video_id:
            video_id = episode_id

        return {
            'id': video_id,
            'display_id': attributes.get('slug'),
            'title': title,
            'description': traverse_obj(attributes, 'description', 'caption'),
            'series': traverse_obj(attributes, 'show_title', 'parent_content_title'),
            'season_number': int_or_none(attributes.get('season_number')),
            'season_id': str_or_none(attributes.get('season_id')),
            'episode': title,
            'episode_number': int_or_none(attributes.get('number')),
            'episode_id': episode_id,
            'channel_id': attributes.get('channel_id'),
            'duration': int_or_none(attributes.get('length')),
            'release_timestamp': parse_iso8601(attributes.get('original_air_date')),
            'thumbnails': thumbnails,
            'availability': self._availability(
                needs_premium=sub_only, needs_subscription=sub_only, needs_auth=sub_only,
                is_private=False, is_unlisted=False),
            'tags': attributes.get('genres'),
        }