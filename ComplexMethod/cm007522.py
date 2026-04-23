def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = (
            self._og_search_title(webpage, default=None)
            or clean_html(get_element_by_class('my_video_title', webpage))
            or self._html_search_regex(r'<title\b[^>]*>([^<]+)</title\b', webpage, 'title'))

        jwplayer_sources = self._parse_json(
            self._search_regex(
                r'''(?s)jwplayer\s*\(\s*['"]mvplayer['"]\s*\)\s*\.\s*setup\s*\(.*?\bsources\s*:\s*(\[.*?])\s*[,});]''', webpage, 'jwplayer sources', fatal=False)
            or '',
            video_id, transform_source=js_to_json, fatal=False)

        formats = self._parse_jwplayer_formats(jwplayer_sources or [], video_id)
        for f in formats or []:
            f['preference'] = self._quality(f['format_id'])
        self._sort_formats(formats)

        description = (
            self._og_search_description(webpage)
            or get_element_by_id('long_desc_holder', webpage)
            or self._html_search_meta('description', webpage))

        uploader = self._search_regex(r'<a[^>]+class="mv_user_name"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False)

        upload_date = get_element_by_class('mv_vid_upl_date', webpage)
        # as ka locale may not be present roll a local date conversion
        upload_date = (unified_strdate(
            # translate any ka month to an en one
            re.sub('|'.join(self._MONTH_NAMES_KA),
                   lambda m: MONTH_NAMES['en'][self._MONTH_NAMES_KA.index(m.group(0))],
                   upload_date, re.I))
            if upload_date else None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': upload_date,
            'view_count': int_or_none(get_element_by_class('mv_vid_views', webpage)),
            'like_count': int_or_none(get_element_by_id('likes_count', webpage)),
            'dislike_count': int_or_none(get_element_by_id('dislikes_count', webpage)),
        }