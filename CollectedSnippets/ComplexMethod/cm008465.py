def _entries(self, sec_uid, user_name, fail_early=False):
        display_id = user_name or sec_uid
        seen_ids = set()

        cursor = int(time.time() * 1E3)
        for page in itertools.count(1):
            for retry in self.RetryManager():
                response = self._download_json(
                    self._API_BASE_URL, display_id, f'Downloading page {page}',
                    query=self._build_web_query(sec_uid, cursor))

                # Avoid infinite loop caused by bad device_id
                # See: https://github.com/yt-dlp/yt-dlp/issues/14031
                current_batch = sorted(traverse_obj(response, ('itemList', ..., 'id', {str})))
                if current_batch and current_batch == sorted(seen_ids):
                    message = 'TikTok API keeps sending the same page'
                    if self._KNOWN_DEVICE_ID:
                        raise ExtractorError(
                            f'{message}. Try again with a different device_id', expected=True)
                    # The user didn't pass a device_id so we can reset it and retry
                    del self._DEVICE_ID
                    retry.error = ExtractorError(
                        f'{message}. Taking measures to avoid an infinite loop', expected=True)

            for video in traverse_obj(response, ('itemList', lambda _, v: v['id'])):
                video_id = video['id']
                if video_id in seen_ids:
                    continue
                seen_ids.add(video_id)
                webpage_url = self._create_url(display_id, video_id)
                yield self.url_result(
                    webpage_url, TikTokIE,
                    **self._parse_aweme_video_web(video, webpage_url, video_id, extract_flat=True))

            old_cursor = cursor
            cursor = traverse_obj(
                response, ('itemList', -1, 'createTime', {lambda x: int(x * 1E3)}))
            if not cursor or old_cursor == cursor:
                # User may not have posted within this ~1 week lookback, so manually adjust cursor
                cursor = old_cursor - 7 * 86_400_000
            # In case 'hasMorePrevious' is wrong, break if we have gone back before TikTok existed
            if cursor < 1472706000000 or not traverse_obj(response, 'hasMorePrevious'):
                return

            # This code path is ideally only reached when one of the following is true:
            # 1. TikTok profile is private and webpage detection was bypassed due to a tiktokuser:sec_uid URL
            # 2. TikTok profile is *not* private but all of their videos are private
            if fail_early and not seen_ids:
                self.raise_login_required(
                    'This user\'s account is likely either private or all of their videos are private. '
                    'Log into an account that has access')