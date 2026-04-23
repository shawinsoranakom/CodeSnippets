def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            response = self._download_json(
                f'https://www.filmon.com/api/vod/movie?id={video_id}',
                video_id)['response']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError):
                errmsg = self._parse_json(e.cause.response.read().decode(), video_id)['reason']
                raise ExtractorError(f'{self.IE_NAME} said: {errmsg}', expected=True)
            raise

        title = response['title']
        description = strip_or_none(response.get('description'))

        if response.get('type_id') == 1:
            entries = [self.url_result('filmon:' + episode_id) for episode_id in response.get('episodes', [])]
            return self.playlist_result(entries, video_id, title, description)

        QUALITY = qualities(('low', 'high'))
        formats = []
        for format_id, stream in response.get('streams', {}).items():
            stream_url = stream.get('url')
            if not stream_url:
                continue
            formats.append({
                'format_id': format_id,
                'url': stream_url,
                'ext': 'mp4',
                'quality': QUALITY(stream.get('quality')),
                'protocol': 'm3u8_native',
            })

        thumbnails = []
        poster = response.get('poster', {})
        thumbs = poster.get('thumbs', {})
        thumbs['poster'] = poster
        for thumb_id, thumb in thumbs.items():
            thumb_url = thumb.get('url')
            if not thumb_url:
                continue
            thumbnails.append({
                'id': thumb_id,
                'url': thumb_url,
                'width': int_or_none(thumb.get('width')),
                'height': int_or_none(thumb.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnails': thumbnails,
        }