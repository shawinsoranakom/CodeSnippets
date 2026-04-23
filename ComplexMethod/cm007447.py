def _real_extract(self, url):
        entity_id = self._match_id(url)
        entity = self._call_api(
            'v1/entities/entity/' + entity_id, entity_id, 'entity')['entity']
        if entity.get('type') == 'activity':
            if entity.get('custom_type') == 'video':
                video_id = entity['entity_guid']
            else:
                return self.url_result(entity['perma_url'])
        else:
            assert (entity['subtype'] == 'video')
            video_id = entity_id
        # 1080p and webm formats available only on the sources array
        video = self._call_api(
            'v2/media/video/' + video_id, video_id, 'video')

        formats = []
        for source in (video.get('sources') or []):
            src = source.get('src')
            if not src:
                continue
            formats.append({
                'format_id': source.get('label'),
                'height': int_or_none(source.get('size')),
                'url': src,
            })
        self._sort_formats(formats)

        entity = video.get('entity') or entity
        owner = entity.get('ownerObj') or {}
        uploader_id = owner.get('username')

        tags = entity.get('tags')
        if tags and isinstance(tags, compat_str):
            tags = [tags]

        thumbnail = None
        poster = video.get('poster') or entity.get('thumbnail_src')
        if poster:
            urlh = self._request_webpage(poster, video_id, fatal=False)
            if urlh:
                thumbnail = urlh.geturl()

        return {
            'id': video_id,
            'title': entity.get('title') or video_id,
            'formats': formats,
            'description': clean_html(entity.get('description')) or None,
            'license': str_or_none(entity.get('license')),
            'timestamp': int_or_none(entity.get('time_created')),
            'uploader': strip_or_none(owner.get('name')),
            'uploader_id': uploader_id,
            'uploader_url': 'https://www.minds.com/' + uploader_id if uploader_id else None,
            'view_count': int_or_none(entity.get('play:count')),
            'like_count': int_or_none(entity.get('thumbs:up:count')),
            'dislike_count': int_or_none(entity.get('thumbs:down:count')),
            'tags': tags,
            'comment_count': int_or_none(entity.get('comments:count')),
            'thumbnail': thumbnail,
        }