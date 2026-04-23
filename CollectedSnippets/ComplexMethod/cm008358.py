def _real_extract(self, url):
        video_id = self._match_id(url)
        url = f'https://17.live/live/{video_id}'

        enter = self._download_json(
            f'https://api-dsa.17app.co/api/v1/lives/{video_id}/enter', video_id,
            headers={'Referer': url}, fatal=False, expected_status=420,
            data=b'\0')
        if enter and enter.get('message') == 'ended':
            raise ExtractorError('This live has ended.', expected=True)

        view_data = self._download_json(
            f'https://api-dsa.17app.co/api/v1/lives/{video_id}', video_id,
            headers={'Referer': url})

        uploader = traverse_obj(
            view_data, ('userInfo', 'displayName'), ('userInfo', 'openID'))

        video_urls = view_data.get('rtmpUrls')
        if not video_urls:
            raise ExtractorError('unable to extract live URL information')
        formats = []
        for (name, value) in video_urls[0].items():
            if not isinstance(value, str):
                continue
            if not value.startswith('http'):
                continue
            quality = -1
            if 'web' in name:
                quality -= 1
            if 'High' in name:
                quality += 4
            if 'Low' in name:
                quality -= 2
            formats.append({
                'format_id': name,
                'url': value,
                'quality': quality,
                'http_headers': {'Referer': url},
                'ext': 'flv',
                'vcodec': 'h264',
                'acodec': 'aac',
            })

        return {
            'id': video_id,
            'title': uploader or video_id,
            'formats': formats,
            'is_live': True,
            'uploader': uploader,
            'uploader_id': video_id,
            'like_count': view_data.get('receivedLikeCount'),
            'view_count': view_data.get('viewerCount'),
            'thumbnail': view_data.get('coverPhoto'),
            'description': view_data.get('caption'),
            'timestamp': view_data.get('beginTime'),
        }