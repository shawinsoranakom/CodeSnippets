def _extract_info(info):
        status = info.get('status')
        if status == 'recording':
            is_live = True
        elif status == 'recorded':
            is_live = False
        else:
            is_live = None
        _QUALITIES = ('small', 'medium', 'large')
        quality_key = qualities(_QUALITIES)
        thumbnails = []
        preview = info.get('preview')
        if isinstance(preview, dict):
            for thumbnail_id, thumbnail_url in preview.items():
                thumbnail_url = url_or_none(thumbnail_url)
                if not thumbnail_url:
                    continue
                if thumbnail_id not in _QUALITIES:
                    continue
                thumbnails.append({
                    'url': thumbnail_url,
                    'preference': quality_key(thumbnail_id),
                })
        return {
            'id': info['_id'],
            'title': info.get('title') or 'Untitled Broadcast',
            'description': info.get('description'),
            'duration': int_or_none(info.get('length')),
            'thumbnails': thumbnails,
            'uploader': info.get('channel', {}).get('display_name'),
            'uploader_id': info.get('channel', {}).get('name'),
            'timestamp': parse_iso8601(info.get('recorded_at')),
            'view_count': int_or_none(info.get('views')),
            'is_live': is_live,
        }