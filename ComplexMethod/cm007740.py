def _real_extract(self, url):
        content_id = self._match_id(url)
        data = self._download_json(
            'https://10play.com.au/api/video/' + content_id, content_id)
        video = data.get('video') or {}
        metadata = data.get('metaData') or {}
        brightcove_id = video.get('videoId') or metadata['showContentVideoId']
        # brightcove_url = smuggle_url(
        #     self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
        #     {'geo_countries': ['AU']})
        m3u8_url = self._request_webpage(HEADRequest(
            self._FASTLY_URL_TEMPL % brightcove_id), brightcove_id).geturl()
        if '10play-not-in-oz' in m3u8_url:
            self.raise_geo_restricted(countries=['AU'])
        formats = self._extract_m3u8_formats(m3u8_url, brightcove_id, 'mp4')
        self._sort_formats(formats)

        return {
            # '_type': 'url_transparent',
            # 'url': brightcove_url,
            'formats': formats,
            'id': brightcove_id,
            'title': video.get('title') or metadata.get('pageContentName') or metadata['showContentName'],
            'description': video.get('description'),
            'age_limit': parse_age_limit(video.get('showRatingClassification') or metadata.get('showProgramClassification')),
            'series': metadata.get('showName'),
            'season': metadata.get('showContentSeason'),
            'timestamp': parse_iso8601(metadata.get('contentPublishDate') or metadata.get('pageContentPublishDate')),
            'thumbnail': video.get('poster'),
            'uploader_id': '2199827728001',
            # 'ie_key': 'BrightcoveNew',
        }