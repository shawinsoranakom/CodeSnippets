def _parse_broadcast_data(self, broadcast, video_id):
        title = broadcast.get('status') or 'Periscope Broadcast'
        uploader = broadcast.get('user_display_name') or broadcast.get('username')
        title = f'{uploader} - {title}' if uploader else title
        thumbnails = [{
            'url': broadcast[image],
        } for image in ('image_url', 'image_url_medium', 'image_url_small') if broadcast.get(image)]

        return {
            'id': broadcast.get('id') or video_id,
            'title': title,
            'timestamp': parse_iso8601(broadcast.get('created_at')) or int_or_none(
                broadcast.get('created_at_ms'), scale=1000),
            'release_timestamp': int_or_none(broadcast.get('scheduled_start_ms'), scale=1000),
            'uploader': uploader,
            'uploader_id': broadcast.get('user_id') or broadcast.get('username'),
            'thumbnails': thumbnails,
            'view_count': int_or_none(broadcast.get('total_watched')),
            'concurrent_view_count': int_or_none(broadcast.get('total_watching')),
            'tags': broadcast.get('tags'),
            'live_status': {
                'running': 'is_live',
                'not_started': 'is_upcoming',
            }.get(traverse_obj(broadcast, ('state', {str.lower}))) or 'was_live',
        }