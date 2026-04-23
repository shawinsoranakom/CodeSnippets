def _entries(self, list_id, display_id):
        query = {
            self._QUERY_NAME: list_id,
            'cursor': 0,
            'count': 20,
            'type': 5,
            'device_id': self._DEVICE_ID,
        }

        for page in itertools.count(1):
            for retry in self.RetryManager():
                try:
                    post_list = self._call_api(
                        self._API_ENDPOINT, display_id, query=query,
                        note=f'Downloading video list page {page}',
                        errnote='Unable to download video list')
                except ExtractorError as e:
                    if isinstance(e.cause, json.JSONDecodeError) and e.cause.pos == 0:
                        retry.error = e
                        continue
                    raise
            for video in post_list.get('aweme_list', []):
                yield {
                    **self._parse_aweme_video_app(video),
                    'extractor_key': TikTokIE.ie_key(),
                    'extractor': 'TikTok',
                    'webpage_url': f'https://tiktok.com/@_/video/{video["aweme_id"]}',
                }
            if not post_list.get('has_more'):
                break
            query['cursor'] = post_list['cursor']