def _real_extract(self, url):
        display_id = self._match_id(url).rpartition('/')[2]
        webpage = self._download_webpage(url, display_id)

        video_data = None
        elements = get_elements_html_by_class('simplestream', webpage)
        for html_tag in elements:
            attributes = extract_attributes(html_tag)
            if 'sidebar' not in (attributes.get('class') or ''):
                video_data = attributes
        if not video_data:
            raise ExtractorError('Could not find video element', expected=True)

        endpoint_url = self._get_ss_endpoint(video_data.get('data-id'), video_data.get('data-env'))

        uvid = video_data['data-uvid']
        video_type = video_data.get('data-type')
        if not video_type or video_type == 'vod':
            video_type = 'show'
        stream_data = self._download_json(
            f'{endpoint_url}/api/{video_type}/stream/{uvid}',
            uvid, 'Downloading stream JSON', query={
                'key': video_data.get('data-key'),
                'platform': self._PLATFORM,
            })
        if traverse_obj(stream_data, 'drm'):
            self.report_drm(uvid)

        return {
            'id': uvid,
            'display_id': display_id,
            'title': self._og_search_title(webpage, default=None),
            'description': self._og_search_description(webpage, default=None),
            'formats': self._extract_m3u8_formats(traverse_obj(stream_data, (
                'response', 'stream', {url_or_none})), uvid, 'mp4'),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'is_live': video_type == 'live',
        }