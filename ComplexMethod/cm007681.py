def _real_extract(self, url):
        video_id = self._match_id(url)
        zvideo = self._download_json(
            'https://www.zhihu.com/api/v4/zvideos/' + video_id, video_id)
        title = zvideo['title']
        video = zvideo.get('video') or {}

        formats = []
        for format_id, q in (video.get('playlist') or {}).items():
            play_url = q.get('url') or q.get('play_url')
            if not play_url:
                continue
            formats.append({
                'asr': int_or_none(q.get('sample_rate')),
                'filesize': int_or_none(q.get('size')),
                'format_id': format_id,
                'fps': int_or_none(q.get('fps')),
                'height': int_or_none(q.get('height')),
                'tbr': float_or_none(q.get('bitrate')),
                'url': play_url,
                'width': int_or_none(q.get('width')),
            })
        self._sort_formats(formats)

        author = zvideo.get('author') or {}
        url_token = author.get('url_token')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': video.get('thumbnail') or zvideo.get('image_url'),
            'uploader': author.get('name'),
            'timestamp': int_or_none(zvideo.get('published_at')),
            'uploader_id': author.get('id'),
            'uploader_url': 'https://www.zhihu.com/people/' + url_token if url_token else None,
            'duration': float_or_none(video.get('duration')),
            'view_count': int_or_none(zvideo.get('play_count')),
            'like_count': int_or_none(zvideo.get('liked_count')),
            'comment_count': int_or_none(zvideo.get('comment_count')),
        }