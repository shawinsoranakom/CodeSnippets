def _parse_gif_data(self, gif_data):
        video_id = gif_data.get('id')
        quality = qualities(tuple(self._FORMATS.keys()))

        orig_height = int_or_none(gif_data.get('height'))
        aspect_ratio = try_get(gif_data, lambda x: orig_height / x['width'])

        formats = []
        for format_id, height in self._FORMATS.items():
            video_url = gif_data['urls'].get(format_id)
            if not video_url:
                continue
            height = min(orig_height, height or orig_height)
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'width': height * aspect_ratio if aspect_ratio else None,
                'height': height,
                'quality': quality(format_id),
            })

        return {
            'id': video_id,
            'webpage_url': f'https://redgifs.com/watch/{video_id}',
            'extractor_key': RedGifsIE.ie_key(),
            'extractor': 'RedGifs',
            'title': ' '.join(gif_data.get('tags') or []) or 'RedGifs',
            'timestamp': int_or_none(gif_data.get('createDate')),
            'uploader': gif_data.get('userName'),
            'duration': int_or_none(gif_data.get('duration')),
            'view_count': int_or_none(gif_data.get('views')),
            'like_count': int_or_none(gif_data.get('likes')),
            'categories': gif_data.get('tags') or [],
            'tags': gif_data.get('tags'),
            'age_limit': 18,
            'formats': formats,
        }