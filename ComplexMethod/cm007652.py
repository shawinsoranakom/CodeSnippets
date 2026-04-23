def _entries(self, user_id, user_name):
        for page_num in itertools.count(1):
            page = self._download_json(
                'https://api.vid.me/videos/%s?user=%s&limit=%d&offset=%d'
                % (self._API_ITEM, user_id, self._LIMIT, (page_num - 1) * self._LIMIT),
                user_name, 'Downloading user %s page %d' % (self._API_ITEM, page_num))

            videos = page.get('videos', [])
            if not videos:
                break

            for video in videos:
                video_url = video.get('full_url') or video.get('embed_url')
                if video_url:
                    yield self.url_result(video_url, VidmeIE.ie_key())

            total = int_or_none(page.get('page', {}).get('total'))
            if total and self._LIMIT * page_num >= total:
                break