def _extract_nodes(self, nodes, is_direct=False):
        for idx, node in enumerate(nodes, start=1):
            if node.get('__typename') != 'GraphVideo' and node.get('is_video') is not True:
                continue

            video_id = node.get('shortcode')

            if is_direct:
                info = {
                    'id': video_id or node['id'],
                    'url': node.get('video_url'),
                    'width': self._get_dimension('width', node),
                    'height': self._get_dimension('height', node),
                    'http_headers': {
                        'Referer': 'https://www.instagram.com/',
                    },
                }
            elif not video_id:
                continue
            else:
                info = {
                    '_type': 'url',
                    'ie_key': 'Instagram',
                    'id': video_id,
                    'url': f'https://instagram.com/p/{video_id}',
                }

            yield {
                **info,
                'title': node.get('title') or (f'Video {idx}' if is_direct else None),
                'description': traverse_obj(
                    node, ('edge_media_to_caption', 'edges', 0, 'node', 'text'), expected_type=str),
                'thumbnail': traverse_obj(
                    node, 'display_url', 'thumbnail_src', 'display_src', expected_type=url_or_none),
                'duration': float_or_none(node.get('video_duration')),
                'timestamp': int_or_none(node.get('taken_at_timestamp')),
                'view_count': int_or_none(node.get('video_view_count')),
                'comment_count': self._get_count(node, 'comments', 'preview_comment', 'to_comment', 'to_parent_comment'),
                'like_count': self._get_count(node, 'likes', 'preview_like'),
            }