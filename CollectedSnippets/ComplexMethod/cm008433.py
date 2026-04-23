def _real_extract(self, url):
        playlist_id = self._match_id(url)

        for retry in self.RetryManager():
            webpage = self._download_webpage(url, playlist_id)
            try:
                data_json = self._search_json(
                    r'var\s?obj\s?=\s?jQuery\.parseJSON\(\'', webpage, 'data', playlist_id,
                    transform_source=js_to_json)
            except ExtractorError as e:
                retry.error = e

        entries = [{
            'id': video['marketPlaceID'],
            'url': video['url'],
            'title': video.get('title'),
            'thumbnail': video.get('thumbUrl') or video.get('thumb'),
            'duration': video.get('durationSeconds'),
            'height': int_or_none(video.get('videoHeight')),
            'width': int_or_none(video.get('videoWidth')),
        } for video in (data_json.get('videos') or []) if video.get('isVideo') and video.get('url')]
        return self.playlist_result(entries, playlist_id=playlist_id, playlist_title=data_json.get('title'))