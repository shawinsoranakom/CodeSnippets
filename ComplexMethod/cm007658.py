def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        page_data = self._parse_json(self._search_regex(
            r'window\.__data\s*=\s*({.*?});', webpage,
            'page data', default='{}'), display_id, fatal=False)
        if not page_data:
            page_data = self._parse_json(self._parse_json(self._search_regex(
                r'window\.__data\s*=\s*JSON\.parse\s*\(\s*(".+?")\s*\)\s*;',
                webpage, 'page data'), display_id), display_id)

        for kind in ('episode', 'clip'):
            current_key = page_data.get(kind, {}).get(
                'current%sKey' % kind.capitalize())
            if not current_key:
                continue
            cache = page_data.get(kind, {}).get('%sCache' % kind, {})
            if not cache:
                continue
            common_data = (cache.get(current_key) or list(cache.values())[0])[kind]
            break
        else:
            raise ExtractorError('Unable to find video data')

        video_data = common_data['video']

        if video_data.get('drm'):
            raise ExtractorError('This video is DRM protected.', expected=True)

        brightcove_id = video_data.get('brightcoveId') or 'ref:' + video_data['referenceId']
        video_id = compat_str(video_data.get('id') or brightcove_id)
        title = common_data['name']

        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail_url,
            'width': int_or_none(thumbnail_id[1:])
        } for thumbnail_id, thumbnail_url in common_data.get('image', {}).get('sizes', {}).items()]

        return {
            '_type': 'url_transparent',
            'url': smuggle_url(
                self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
                {'geo_countries': self._GEO_COUNTRIES}),
            'id': video_id,
            'title': title,
            'description': common_data.get('description'),
            'duration': float_or_none(video_data.get('duration'), 1000),
            'thumbnails': thumbnails,
            'ie_key': 'BrightcoveNew',
        }