def _real_extract(self, url):
        display_id, video_id = self._match_valid_url(url).group('slug', 'id')
        if video_id:
            display_id = video_id
        webpage = self._download_webpage(url, display_id)

        password_form = self._search_regex(
            r'(?is)<form[^>]+?method=["\']post["\'][^>]*>(.+?password.+?)</form>',
            webpage, 'password form', default=None)
        if password_form:
            try:
                webpage = self._download_webpage(url, display_id, data=urlencode_postdata({
                    'password': self._get_video_password(),
                    **self._hidden_inputs(password_form),
                }), note='Logging in with video password')
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 418:
                    raise ExtractorError('Wrong video password', expected=True)
                raise

        description = None
        # even if we have video_id, some videos require player URL with portfolio_id query param
        # https://github.com/ytdl-org/youtube-dl/issues/20070
        vimeo_url = VimeoIE._extract_url(url, webpage)
        if vimeo_url:
            description = self._html_search_meta('description', webpage, default=None)
        elif video_id:
            vimeo_url = f'https://vimeo.com/{video_id}'
        else:
            raise ExtractorError(
                'No Vimeo embed or video ID could be found in VimeoPro page', expected=True)

        return self.url_result(vimeo_url, VimeoIE, video_id, url_transparent=True,
                               description=description)