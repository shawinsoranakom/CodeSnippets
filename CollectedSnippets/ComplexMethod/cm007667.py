def _real_extract(self, url):
        video_id = self._match_id(url)

        # Provides more metadata
        webpage = self._download_webpage(url, video_id, fatal=False)

        if not webpage:
            webpage = self._download_webpage(
                'http://www.aparat.com/video/video/embed/vt/frame/showvideo/yes/videohash/' + video_id,
                video_id)

        options = self._parse_json(self._search_regex(
            r'options\s*=\s*({.+?})\s*;', webpage, 'options'), video_id)

        formats = []
        for sources in (options.get('multiSRC') or []):
            for item in sources:
                if not isinstance(item, dict):
                    continue
                file_url = url_or_none(item.get('src'))
                if not file_url:
                    continue
                item_type = item.get('type')
                if item_type == 'application/vnd.apple.mpegurl':
                    formats.extend(self._extract_m3u8_formats(
                        file_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                else:
                    ext = mimetype2ext(item.get('type'))
                    label = item.get('label')
                    formats.append({
                        'url': file_url,
                        'ext': ext,
                        'format_id': 'http-%s' % (label or ext),
                        'height': int_or_none(self._search_regex(
                            r'(\d+)[pP]', label or '', 'height',
                            default=None)),
                    })
        self._sort_formats(
            formats, field_preference=('height', 'width', 'tbr', 'format_id'))

        info = self._search_json_ld(webpage, video_id, default={})

        if not info.get('title'):
            info['title'] = get_element_by_id('videoTitle', webpage) or \
                self._html_search_meta(['og:title', 'twitter:title', 'DC.Title', 'title'], webpage, fatal=True)

        return merge_dicts(info, {
            'id': video_id,
            'thumbnail': url_or_none(options.get('poster')),
            'duration': int_or_none(options.get('duration')),
            'formats': formats,
        })