def _real_extract(self, url):
        video_id, secret = self._match_valid_url(url).groups()

        query = {
            'video_id': video_id,
            'key': 'v0vhrt7bg2xq1vyxhkct',
        }
        if secret:
            query['secret'] = secret

        data = self._download_json(
            'http://api.viddler.com/api/v2/viddler.videos.getPlaybackDetails.json',
            video_id, headers={'Referer': url}, query=query)['video']

        formats = []
        for filed in data['files']:
            if filed.get('status', 'ready') != 'ready':
                continue
            format_id = filed.get('profile_id') or filed['profile_name']
            f = {
                'format_id': format_id,
                'format_note': filed['profile_name'],
                'url': self._proto_relative_url(filed['url']),
                'width': int_or_none(filed.get('width')),
                'height': int_or_none(filed.get('height')),
                'filesize': int_or_none(filed.get('size')),
                'ext': filed.get('ext'),
                'source_preference': -1,
            }
            formats.append(f)

            if filed.get('cdn_url'):
                f = f.copy()
                f['url'] = self._proto_relative_url(filed['cdn_url'], 'http:')
                f['format_id'] = format_id + '-cdn'
                f['source_preference'] = 1
                formats.append(f)

            if filed.get('html5_video_source'):
                f = f.copy()
                f['url'] = self._proto_relative_url(filed['html5_video_source'])
                f['format_id'] = format_id + '-html5'
                f['source_preference'] = 0
                formats.append(f)

        categories = [
            t.get('text') for t in data.get('tags', []) if 'text' in t]

        return {
            'id': video_id,
            'title': data['title'],
            'formats': formats,
            'description': data.get('description'),
            'timestamp': int_or_none(data.get('upload_time')),
            'thumbnail': self._proto_relative_url(data.get('thumbnail_url')),
            'uploader': data.get('author'),
            'duration': float_or_none(data.get('length')),
            'view_count': int_or_none(data.get('view_count')),
            'comment_count': int_or_none(data.get('comment_count')),
            'categories': categories,
        }