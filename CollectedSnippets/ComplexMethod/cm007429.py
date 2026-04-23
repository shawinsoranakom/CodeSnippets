def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.vidlii.com/watch?v=%s' % video_id, video_id)

        formats = []

        def add_format(format_url, height=None):
            height = int(self._search_regex(r'(\d+)\.mp4',
                         format_url, 'height', default=360))

            formats.append({
                'url': format_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
            })

        sources = re.findall(
            r'src\s*:\s*(["\'])(?P<url>(?:https?://)?(?:(?!\1).)+)\1',
            webpage)

        formats = []
        if len(sources) > 1:
            add_format(sources[1][1])
            self._check_formats(formats, video_id)
        if len(sources) > 0:
            add_format(sources[0][1])

        self._sort_formats(formats)

        title = self._html_search_regex(
            (r'<h1>([^<]+)</h1>', r'<title>([^<]+) - VidLii<'), webpage,
            'title')

        description = self._html_search_meta(
            ('description', 'twitter:description'), webpage,
            default=None) or strip_or_none(
            get_element_by_id('des_text', webpage))

        thumbnail = self._html_search_meta(
            'twitter:image', webpage, default=None)
        if not thumbnail:
            thumbnail_path = self._search_regex(
                r'img\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'thumbnail', fatal=False, group='url')
            if thumbnail_path:
                thumbnail = urljoin(url, thumbnail_path)

        uploader = self._search_regex(
            r'<div[^>]+class=["\']wt_person[^>]+>\s*<a[^>]+\bhref=["\']/user/[^>]+>([^<]+)',
            webpage, 'uploader', fatal=False)
        uploader_url = 'https://www.vidlii.com/user/%s' % uploader if uploader else None

        upload_date = unified_strdate(self._html_search_meta(
            'datePublished', webpage, default=None) or self._search_regex(
            r'<date>([^<]+)', webpage, 'upload date', fatal=False))

        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'duration',
            default=None) or self._search_regex(
            r'duration\s*:\s*(\d+)', webpage, 'duration', fatal=False))

        view_count = str_to_int(self._html_search_regex(
            (r'<strong>([\d,.]+)</strong> views',
             r'Views\s*:\s*<strong>([\d,.]+)</strong>'),
            webpage, 'view count', fatal=False))

        comment_count = int_or_none(self._search_regex(
            (r'<span[^>]+id=["\']cmt_num[^>]+>(\d+)',
             r'Comments\s*:\s*<strong>(\d+)'),
            webpage, 'comment count', fatal=False))

        average_rating = float_or_none(self._search_regex(
            r'rating\s*:\s*([\d.]+)', webpage, 'average rating', fatal=False))

        category = self._html_search_regex(
            r'<div>Category\s*:\s*</div>\s*<div>\s*<a[^>]+>([^<]+)', webpage,
            'category', fatal=False)
        categories = [category] if category else None

        tags = [
            strip_or_none(tag)
            for tag in re.findall(
                r'<a[^>]+\bhref=["\']/results\?.*?q=[^>]*>([^<]+)',
                webpage) if strip_or_none(tag)
        ] or None

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'categories': categories,
            'tags': tags,
        }