def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('display_id')
        video_id = mobj.group('video_id').replace('/', '-')
        webpage = self._download_webpage(url, video_id)

        source, img = self._search_regex(r'(?s)(?P<source><source[^>]*>)(?P<img><img[^>]*>)',
                                         webpage, 'video', group=('source', 'img'))
        source = extract_attributes(source)
        img = extract_attributes(img)

        raw_json_ld = list(self._yield_json_ld(webpage, video_id))
        json_ld = self._json_ld(raw_json_ld, video_id)
        json_ld.pop('url', None)

        ism_manifest_url = (
            source.get('src')
            or next(json_ld.get('embedUrl') for json_ld in raw_json_ld if json_ld.get('@type') == 'VideoObject')
        )
        formats, subtitles = self._extract_ism_formats_and_subtitles(ism_manifest_url, video_id)

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title':
                self._html_search_regex(r'<h1><span class="title">([^<]*)</span>',
                                        webpage, 'headline', default=None)
                or img.get('title') or json_ld.get('title') or self._og_search_title(webpage)
                or remove_end(self._html_extract_title(webpage), ' -'),
            'alt_title': img.get('alt'),
            'description': json_ld.get('description') or self._og_search_description(webpage),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': [{'url': img['src']}] if 'src' in img else json_ld.get('thumbnails'),
        }, json_ld)