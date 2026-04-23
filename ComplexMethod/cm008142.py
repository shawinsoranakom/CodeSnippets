def _real_extract(self, url):
        page_type, video_id = self._match_valid_url(url).groups()
        if page_type == 'clip':
            page_type = 'episode'

        playout = self._call_api(
            'playout/new/url/' + video_id, video_id)['playout']

        if not self.get_param('allow_unplayable_formats') and playout.get('drm'):
            self.report_drm(video_id)

        formats = self._extract_m3u8_formats(re.sub(
            # https://docs.aws.amazon.com/mediapackage/latest/ug/manifest-filtering.html
            r'aws\.manifestfilter=[\w:;,-]+&?',
            '', playout['url']), video_id, 'mp4')

        # video = self._call_api(
        #     'product/id', video_id, {
        #         'id': video_id,
        #         'productType': 'ASSET',
        #         'productSubType': page_type.upper()
        #     })['productModel']

        response = self._download_json(
            f'http://api.shahid.net/api/v1_1/{page_type}/{video_id}',
            video_id, 'Downloading video JSON', query={
                'apiKey': 'sh@hid0nlin3',
                'hash': 'b2wMCTHpSmyxGqQjJFOycRmLSex+BpTK/ooxy6vHaqs=',
            })
        data = response.get('data', {})
        error = data.get('error')
        if error:
            raise ExtractorError(
                '{} returned error: {}'.format(self.IE_NAME, '\n'.join(error.values())),
                expected=True)

        video = data[page_type]
        title = video['title']
        categories = [
            category['name']
            for category in video.get('genres', []) if 'name' in category]

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': video.get('thumbnailUrl'),
            'duration': int_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('referenceDate')),
            'categories': categories,
            'series': video.get('showTitle') or video.get('showName'),
            'season': video.get('seasonTitle'),
            'season_number': int_or_none(video.get('seasonNumber')),
            'season_id': str_or_none(video.get('seasonId')),
            'episode_number': int_or_none(video.get('number')),
            'episode_id': video_id,
            'formats': formats,
        }