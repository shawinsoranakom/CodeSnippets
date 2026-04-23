def _real_extract(self, url):
        user_name, sec_uid = self._match_id(url), None
        if re.fullmatch(r'MS4wLjABAAAA[\w-]{64}', user_name):
            user_name, sec_uid = None, user_name
            fail_early = True
        else:
            webpage = self._download_webpage(
                self._UPLOADER_URL_FORMAT % user_name, user_name,
                'Downloading user webpage', 'Unable to download user webpage',
                fatal=False, impersonate=True) or ''
            detail = traverse_obj(
                self._get_universal_data(webpage, user_name), ('webapp.user-detail', {dict})) or {}
            video_count = traverse_obj(detail, ('userInfo', ('stats', 'statsV2'), 'videoCount', {int}, any))
            if not video_count and detail.get('statusCode') == 10222:
                self.raise_login_required(
                    'This user\'s account is private. Log into an account that has access')
            elif video_count == 0:
                raise ExtractorError('This account does not have any videos posted', expected=True)
            sec_uid = traverse_obj(detail, ('userInfo', 'user', 'secUid', {str}))
            if sec_uid:
                fail_early = not traverse_obj(detail, ('userInfo', 'itemList', ...))
            else:
                sec_uid = self._extract_sec_uid_from_embed(user_name)
                fail_early = False

        if not sec_uid:
            raise ExtractorError(
                'Unable to extract secondary user ID. If you are able to get the channel_id '
                'from a video posted by this user, try using "tiktokuser:channel_id" as the '
                'input URL (replacing `channel_id` with its actual value)', expected=True)

        return self.playlist_result(self._entries(sec_uid, user_name, fail_early), sec_uid, user_name)