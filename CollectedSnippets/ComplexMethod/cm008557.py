def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            f'https://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/{video_id}/',
            video_id, query={'_': time_seconds()})['data']

        video_urls = []

        video_files = video.get('video_files')
        if isinstance(video_files, list):
            video_urls.extend(video_files)
        elif isinstance(video_files, dict):
            video_urls.extend(video_files.values())

        video_urls = list(set(video_urls))

        filesh = video.get('filesh') or {}

        formats = []
        for video_url in video_urls:
            height = int_or_none(self._search_regex(
                r'\.(\d{3,4})\.mp4(?:\?|$)', video_url, 'height', default=None))
            if not height and len(filesh) == 1:
                height = int_or_none(next(iter(filesh.keys())))
            token = filesh.get(str(height))
            if token is None:
                continue
            formats.append({
                'url': update_url_query(video_url, {'token': token}),
                'height': height,
            })

        timestamp = video.get('date')
        if timestamp:
            # upload date is in CEST
            timestamp = parse_iso8601(timestamp + ' +0200', ' ')

        thumbnails = [{
            'url': self._proto_relative_url(thumbnail),
        } for thumbnail in video.get('thumbnails', [])]

        tags = [tag['title'] for tag in video.get('tags') or []]

        return {
            'id': video.get('id') or video_id,
            'title': video.get('title'),
            'description': video.get('description'),
            'thumbnails': thumbnails,
            'uploader': video.get('user_name'),
            'uploader_id': video.get('user_id'),
            'timestamp': timestamp,
            'duration': int_or_none(video.get('length')),
            'age_limit': parse_age_limit(video.get('age_limit')),
            'tags': tags,
            'formats': formats,
        }