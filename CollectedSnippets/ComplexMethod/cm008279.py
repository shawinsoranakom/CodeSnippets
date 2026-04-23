def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if any(p in webpage for p in (
            '<title>404 - MOTHERLESS.COM<',
            ">The page you're looking for cannot be found.<",
            '<div class="error-page',
        )):
            raise ExtractorError(f'Video {video_id} does not exist', expected=True)

        if '>The content you are trying to view is for friends only.' in webpage:
            raise ExtractorError(f'Video {video_id} is for friends only', expected=True)

        title = self._html_search_regex(
            (r'(?s)<div[^>]+\bclass=["\']media-meta-title[^>]+>(.+?)</div>',
             r'id="view-upload-title">\s+([^<]+)<'), webpage, 'title')
        video_url = (self._html_search_regex(
            (r'setup\(\{\s*["\']file["\']\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1',
             r'fileurl\s*=\s*(["\'])(?P<url>(?:(?!\1).)+)\1'),
            webpage, 'video URL', default=None, group='url')
            or f'http://cdn4.videos.motherlessmedia.com/videos/{video_id}.mp4?fs=opencloud')
        age_limit = self._rta_search(webpage)
        view_count = str_to_int(self._html_search_regex(
            (r'>([\d,.]+)\s+Views<', r'<strong>Views</strong>\s+([^<]+)<'),
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._html_search_regex(
            (r'>([\d,.]+)\s+Favorites<',
             r'<strong>Favorited</strong>\s+([^<]+)<'),
            webpage, 'like count', fatal=False))

        upload_date = unified_strdate(self._search_regex(
            r'class=["\']count[^>]+>(\d+\s+[a-zA-Z]{3}\s+\d{4})<', webpage,
            'upload date', default=None))
        if not upload_date:
            uploaded_ago = self._search_regex(
                r'>\s*(\d+[hd])\s+[aA]go\b', webpage, 'uploaded ago',
                default=None)
            if uploaded_ago:
                delta = int(uploaded_ago[:-1])
                _AGO_UNITS = {
                    'h': 'hours',
                    'd': 'days',
                }
                kwargs = {_AGO_UNITS.get(uploaded_ago[-1]): delta}
                upload_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(**kwargs)).strftime('%Y%m%d')

        comment_count = len(re.findall(r'''class\s*=\s*['"]media-comment-contents\b''', webpage))
        uploader_id = self._html_search_regex(
            (r'''<span\b[^>]+\bclass\s*=\s*["']username\b[^>]*>([^<]+)</span>''',
             r'''(?s)['"](?:media-meta-member|thumb-member-username)\b[^>]+>\s*<a\b[^>]+\bhref\s*=\s*['"]/m/([^"']+)'''),
            webpage, 'uploader_id', fatal=False)
        categories = self._html_search_meta('keywords', webpage, default='')
        categories = [cat.strip() for cat in categories.split(',') if cat.strip()]

        return {
            'id': video_id,
            'title': title,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'categories': categories,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'age_limit': age_limit,
            'url': video_url,
        }