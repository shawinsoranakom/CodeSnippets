def _extract_video_from_id(self, video_id):
        # Authorization generation algorithm is reverse engineered from `signer` in
        # http://graphics8.nytimes.com/video/vhs/vhs-2.x.min.js
        path = '/svc/video/api/v3/video/' + video_id
        hm = hmac.new(self._SECRET, (path + ':vhs').encode(), hashlib.sha512).hexdigest()
        video_data = self._download_json('http://www.nytimes.com' + path, video_id, 'Downloading video JSON', headers={
            'Authorization': 'NYTV ' + base64.b64encode(hm.encode()).decode(),
            'X-NYTV': 'vhs',
        }, fatal=False)
        if not video_data:
            video_data = self._download_json(
                'http://www.nytimes.com/svc/video/api/v2/video/' + video_id,
                video_id, 'Downloading video JSON')

        title = video_data['headline']

        def get_file_size(file_size):
            if isinstance(file_size, int):
                return file_size
            elif isinstance(file_size, dict):
                return int(file_size.get('value', 0))
            else:
                return None

        urls = []
        formats = []
        for video in video_data.get('renditions', []):
            video_url = video.get('url')
            format_id = video.get('type')
            if not video_url or format_id == 'thumbs' or video_url in urls:
                continue
            urls.append(video_url)
            ext = mimetype2ext(video.get('mimetype')) or determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id or 'hls', fatal=False))
            elif ext == 'mpd':
                continue
            #     formats.extend(self._extract_mpd_formats(
            #         video_url, video_id, format_id or 'dash', fatal=False))
            else:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'vcodec': video.get('videoencoding') or video.get('video_codec'),
                    'width': int_or_none(video.get('width')),
                    'height': int_or_none(video.get('height')),
                    'filesize': get_file_size(video.get('file_size') or video.get('fileSize')),
                    'tbr': int_or_none(video.get('bitrate'), 1000) or None,
                    'ext': ext,
                })
        self._sort_formats(formats, ('height', 'width', 'filesize', 'tbr', 'fps', 'format_id'))

        thumbnails = []
        for image in video_data.get('images', []):
            image_url = image.get('url')
            if not image_url:
                continue
            thumbnails.append({
                'url': 'http://www.nytimes.com/' + image_url,
                'width': int_or_none(image.get('width')),
                'height': int_or_none(image.get('height')),
            })

        publication_date = video_data.get('publication_date')
        timestamp = parse_iso8601(publication_date[:-8]) if publication_date else None

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('summary'),
            'timestamp': timestamp,
            'uploader': video_data.get('byline'),
            'duration': float_or_none(video_data.get('duration'), 1000),
            'formats': formats,
            'thumbnails': thumbnails,
        }