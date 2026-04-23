def _real_extract(self, url):
        main_id, type_ = re.match(self._VALID_URL, url).group('id', 'type')
        webpage = self._download_webpage(url, main_id)

        title = self._html_search_regex(
            r'<title\b[^>]*?>(?:Video:\s+)?(.+?)(?:\s+-\s+ThisVid(?:\.com| tube))?</title>',
            webpage, 'title')

        if type_ == 'embed':
            # look for more metadata
            video_alt_url = url_or_none(self._search_regex(
                r'''video_alt_url\s*:\s+'(%s/)',''' % (self._VALID_URL, ),
                webpage, 'video_alt_url', default=None))
            if video_alt_url and video_alt_url != url:
                webpage = self._download_webpage(
                    video_alt_url, main_id,
                    note='Redirecting embed to main page', fatal=False) or webpage

        video_holder = get_element_by_class('video-holder', webpage) or ''
        if '>This video is a private video' in video_holder:
            self.raise_login_required(
                (clean_html(video_holder) or 'Private video').split('\n', 1)[0])

        uploader = self._html_search_regex(
            r'''(?s)<span\b[^>]*>Added by:\s*</span><a\b[^>]+\bclass\s*=\s*["']author\b[^>]+\bhref\s*=\s*["']https://thisvid\.com/members/([0-9]+/.{3,}?)\s*</a>''',
            webpage, 'uploader', default='')
        uploader = re.split(r'''/["'][^>]*>\s*''', uploader)
        if len(uploader) == 2:
            # id must be non-empty, uploader could be ''
            uploader_id, uploader = uploader
            uploader = uploader or None
        else:
            uploader_id = uploader = None

        return merge_dicts({
            '_type': 'url_transparent',
            'title': title,
            'age_limit': 18,
            'uploader': uploader,
            'uploader_id': uploader_id,
        }, self.url_result(url, ie='Generic'))