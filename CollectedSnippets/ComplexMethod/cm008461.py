def _extract_web_data_and_status(self, url, video_id, fatal=True):
        video_data, status = {}, -1

        def get_webpage(note='Downloading webpage'):
            res = self._download_webpage_handle(url, video_id, note, fatal=fatal, impersonate=True)
            if res is False:
                return False

            webpage, urlh = res
            if urllib.parse.urlparse(urlh.url).path == '/login':
                message = 'TikTok is requiring login for access to this content'
                if fatal:
                    self.raise_login_required(message)
                self.report_warning(f'{message}. {self._login_hint()}', video_id=video_id)
                return False

            return webpage

        webpage = get_webpage()
        if webpage is False:
            return video_data, status

        universal_data = self._get_universal_data(webpage, video_id)
        if not universal_data:
            try:
                cookie_names = self._solve_challenge_and_set_cookies(webpage)
            except ExtractorError as e:
                if fatal:
                    raise
                self.report_warning(e.orig_msg, video_id=video_id)
                return video_data, status

            webpage = get_webpage(note='Downloading webpage with challenge cookie')
            # Manually clear challenge cookies that should expire immediately after webpage request
            for cookie_name in filter(None, cookie_names):
                self.cookiejar.clear(domain='.tiktok.com', path='/', name=cookie_name)
            if webpage is False:
                return video_data, status
            universal_data = self._get_universal_data(webpage, video_id)

        if not universal_data:
            message = 'Unable to extract universal data for rehydration'
            if fatal:
                raise ExtractorError(message)
            self.report_warning(message, video_id=video_id)
            return video_data, status

        status = traverse_obj(universal_data, ('webapp.video-detail', 'statusCode', {int})) or 0
        video_data = traverse_obj(universal_data, ('webapp.video-detail', 'itemInfo', 'itemStruct', {dict}))

        if not traverse_obj(video_data, ('video', {dict})) and traverse_obj(video_data, ('isContentClassified', {bool})):
            message = 'This post may not be comfortable for some audiences. Log in for access'
            if fatal:
                self.raise_login_required(message)
            self.report_warning(f'{message}. {self._login_hint()}', video_id=video_id)

        return video_data, status