def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        attrs = extract_attributes(get_element_html_by_attribute('type', 'VideoStream', webpage) or '')
        direct_url = attrs['data-vid']

        metadata = self._download_json(
            'https://api.kinghub.vn/video/api/v1/detailVideoByGet?FileName={}'.format(
                remove_start(direct_url, 'kenh14cdn.com/')), video_id, fatal=False)

        formats = [{'url': f'https://{direct_url}', 'format_id': 'http', 'quality': 1}]
        subtitles = {}
        video_data = self._download_json(
            f'https://{direct_url}.json', video_id, note='Downloading video data', fatal=False)
        if hls_url := traverse_obj(video_data, ('hls', {url_or_none})):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if dash_url := traverse_obj(video_data, ('mpd', {url_or_none})):
            fmts, subs = self._extract_mpd_formats_and_subtitles(
                dash_url, video_id, mpd_id='dash', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            **traverse_obj(metadata, {
                'duration': ('duration', {parse_duration}),
                'uploader': ('author', {strip_or_none}),
                'timestamp': ('uploadtime', {parse_iso8601(delimiter=' ')}),
                'view_count': ('views', {int_or_none}),
            }),
            'id': video_id,
            'title': (
                traverse_obj(metadata, ('title', {strip_or_none}))
                or clean_html(self._og_search_title(webpage))
                or clean_html(get_element_by_class('vdbw-title', webpage))),
            'formats': formats,
            'subtitles': subtitles,
            'description': (
                clean_html(self._og_search_description(webpage))
                or clean_html(get_element_by_class('vdbw-sapo', webpage))),
            'thumbnail': (self._og_search_thumbnail(webpage) or attrs.get('data-thumb')),
            'tags': traverse_obj(self._html_search_meta('keywords', webpage), (
                {lambda x: x.split(';')}, ..., filter)),
        }