def _real_extract(self, url):
        video_id = self._match_id(url)

        for retry in self.RetryManager():
            webpage = self._download_webpage(url, video_id)
            review_body = get_element_by_attribute('data-hook', 'review-body', webpage)
            if not review_body:
                retry.error = ExtractorError('Review body was not found in webpage', expected=True)

        formats, subtitles = [], {}

        manifest_url = self._search_regex(
            r'data-video-url="([^"]+)"', review_body, 'm3u8 url', default=None)
        if url_or_none(manifest_url):
            fmts, subtitles = self._extract_m3u8_formats_and_subtitles(
                manifest_url, video_id, 'mp4', fatal=False)
            formats.extend(fmts)

        video_url = self._search_regex(
            r'<input[^>]+\bvalue="([^"]+)"[^>]+\bclass="video-url"', review_body, 'mp4 url', default=None)
        if url_or_none(video_url):
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': 'http-mp4',
            })

        if not formats:
            self.raise_no_formats('No video found for this customer review', expected=True)

        return {
            'id': video_id,
            'title': (clean_html(get_element_by_attribute('data-hook', 'review-title', webpage))
                      or self._html_extract_title(webpage)),
            'description': clean_html(traverse_obj(re.findall(
                r'<span(?:\s+class="cr-original-review-content")?>(.+?)</span>', review_body), -1)),
            'uploader': clean_html(get_element_by_class('a-profile-name', webpage)),
            'average_rating': float_or_none(clean_html(get_element_by_attribute(
                'data-hook', 'review-star-rating', webpage) or '').partition(' ')[0]),
            'thumbnail': self._search_regex(
                r'data-thumbnail-url="([^"]+)"', review_body, 'thumbnail', default=None),
            'formats': formats,
            'subtitles': subtitles,
        }