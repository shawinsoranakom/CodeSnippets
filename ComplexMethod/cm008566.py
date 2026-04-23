def _real_extract(self, url):
        media_id = self._match_id(url)
        try:
            webpage = self._download_webpage(url, media_id)
        except ExtractorError as error:
            if isinstance(error.cause, HTTPError) and error.cause.status == 401:
                self.raise_login_required()
            raise

        media_url_string = self._search_regex(
            r'embedController\(\[{"url"\s*:\s*("[^"]+"),', webpage, 'media url', default=None)
        if media_url_string:
            uploader = None
            formats = [{
                'url': self._parse_json(media_url_string, media_id),
                'format_id': 'source',
                'quality': 1,
            }]

        else:
            json_video = self._download_json(f'https://www.newgrounds.com/portal/video/{media_id}', media_id, headers={
                'Accept': 'application/json',
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest',
            })

            formats = []
            uploader = traverse_obj(json_video, ('author', {str}))
            for format_id, sources in traverse_obj(json_video, ('sources', {dict.items}, ...)):
                quality = int_or_none(format_id[:-1])
                formats.extend({
                    'format_id': format_id,
                    'quality': quality,
                    'url': url,
                } for url in traverse_obj(sources, (..., 'src', {url_or_none})))

        if not uploader:
            uploader = self._html_search_regex(
                (r'(?s)<h4[^>]*>(.+?)</h4>.*?<em>\s*(?:Author|Artist)\s*</em>',
                 r'(?:Author|Writer)\s*<a[^>]+>([^<]+)'), webpage, 'uploader',
                fatal=False)

        if len(formats) == 1:
            formats[0]['filesize'] = int_or_none(self._html_search_regex(
                r'"filesize"\s*:\s*["\']?([\d]+)["\']?,', webpage, 'filesize', default=None))

            video_type_description = self._html_search_regex(
                r'"description"\s*:\s*["\']?([^"\']+)["\']?,', webpage, 'media type', default=None)
            if video_type_description == 'Audio File':
                formats[0]['vcodec'] = 'none'

        self._check_formats(formats, media_id)
        return {
            'id': media_id,
            'title': self._html_extract_title(webpage),
            'uploader': uploader,
            'timestamp': unified_timestamp(self._search_regex(
                r'itemprop="(?:uploadDate|datePublished)"\s+content="([^"]+)"',
                webpage, 'timestamp', default=None)),
            'duration': parse_duration(self._html_search_regex(
                r'"duration"\s*:\s*["\']?(\d+)["\']?', webpage, 'duration', default=None)),
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': (
                clean_html(get_element_by_id('author_comments', webpage))
                or self._og_search_description(webpage)),
            'age_limit': self._AGE_LIMIT.get(self._html_search_regex(
                r'<h2\s+class=["\']rated-([etma])["\']', webpage, 'age_limit', default='e')),
            'view_count': parse_count(self._html_search_regex(
                r'(?s)<dt>\s*(?:Views|Listens)\s*</dt>\s*<dd>([\d\.,]+)</dd>',
                webpage, 'view count', default=None)),
        }