def _real_extract(self, url):
        video_type, video_id, display_id = self._match_valid_url(url).group('type', 'id', 'slug')
        webpage = self._download_webpage(url, video_id)
        if video_type == 'player':
            real_url = self._og_search_url(webpage)
            if not self.suitable(real_url) or self._match_valid_url(real_url).group('type') == 'player':
                raise UnsupportedError(real_url)
            return self.url_result(real_url, self.ie_key())

        upload_date = None
        date_elements = traverse_obj(webpage, (
            {find_element(cls='article-item__date')}, {clean_html}, filter, {str.split}))
        if date_elements and len(date_elements) == 3:
            day, month, year = date_elements
            day = int_or_none(day.rstrip('.'))
            month = month_by_name(month, 'is')
            if day and month and re.fullmatch(r'[0-9]{4}', year):
                upload_date = f'{year}{month:02d}{day:02d}'

        player = self._search_json(
            r'App\.Player\.Init\(', webpage, video_id, 'player', transform_source=js_to_json)
        m3u8_url = traverse_obj(player, ('File', {urljoin('https://vod.visir.is/')}))

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': self._extract_m3u8_formats(m3u8_url, video_id, 'mp4'),
            'upload_date': upload_date,
            **traverse_obj(webpage, ({find_element(cls='article-item press-ads')}, {
                'description': ({find_element(cls='-large')}, {clean_html}, filter),
                'view_count': ({find_element(cls='article-item__viewcount')}, {clean_html}, {int_or_none}),
            })),
            **traverse_obj(player, {
                'title': ('Title', {clean_html}),
                'categories': ('Categoryname', {clean_html}, filter, all, filter),
                'duration': ('MediaDuration', {int_or_none}),
                'thumbnail': ('Image', {url_or_none}),
            }),
        }