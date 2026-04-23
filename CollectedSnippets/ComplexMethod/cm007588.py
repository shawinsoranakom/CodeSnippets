def _parse_broadcast_data(self, broadcast, video_id):
        title = broadcast.get('status') or 'Periscope Broadcast'
        uploader = broadcast.get('user_display_name') or broadcast.get('username')
        title = '%s - %s' % (uploader, title) if uploader else title
        is_live = broadcast.get('state').lower() == 'running'

        thumbnails = [{
            'url': broadcast[image],
        } for image in ('image_url', 'image_url_small') if broadcast.get(image)]

        return {
            'id': broadcast.get('id') or video_id,
            'title': self._live_title(title) if is_live else title,
            'timestamp': parse_iso8601(broadcast.get('created_at')),
            'uploader': uploader,
            'uploader_id': broadcast.get('user_id') or broadcast.get('username'),
            'thumbnails': thumbnails,
            'view_count': int_or_none(broadcast.get('total_watched')),
            'tags': broadcast.get('tags'),
            'is_live': is_live,
        }