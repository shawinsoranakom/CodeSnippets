def _real_extract(self, url):
        user_id = self._match_id(url)

        info_raw = self._download_json(
            'https://bigo.tv/studio/getInternalStudioInfo',
            user_id, data=urlencode_postdata({'siteId': user_id}))

        if not isinstance(info_raw, dict):
            raise ExtractorError('Received invalid JSON data')
        if info_raw.get('code'):
            raise ExtractorError(
                'Bigo says: %s (code %s)' % (info_raw.get('msg'), info_raw.get('code')), expected=True)
        info = info_raw.get('data') or {}

        if not info.get('alive'):
            raise ExtractorError('This user is offline.', expected=True)

        return {
            'id': info.get('roomId') or user_id,
            'title': info.get('roomTopic') or info.get('nick_name') or user_id,
            'formats': [{
                'url': info.get('hls_src'),
                'ext': 'mp4',
                'protocol': 'm3u8',
            }],
            'thumbnail': info.get('snapshot'),
            'uploader': info.get('nick_name'),
            'uploader_id': user_id,
            'is_live': True,
        }