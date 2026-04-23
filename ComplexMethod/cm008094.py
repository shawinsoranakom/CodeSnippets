def _real_extract(self, url):
        program_id = self._match_id(url)
        try:
            programs = self._download_json(
                f'{self._BASE_URL}/web_api/programs/{program_id}', program_id)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 404:
                raise ExtractorError('Invalid URL', expected=True)
            raise

        query = {k: v[-1] for k, v in parse_qs(url).items() if v}
        if 'c' not in query:
            entries = [
                self.url_result(update_url_query(url, {'c': self._get_encoded_id(program)}), OnsenIE)
                for program in traverse_obj(programs, ('contents', lambda _, v: v['id']))
            ]

            return self.playlist_result(
                entries, program_id, traverse_obj(programs, ('program_info', 'title', {clean_html})))

        raw_id = base64.urlsafe_b64decode(f'{query["c"]}===').decode()
        p_keys = ('contents', lambda _, v: v['id'] == int(raw_id))

        program = traverse_obj(programs, (*p_keys, any))
        if not program:
            raise ExtractorError(
                'This program is no longer available', expected=True)
        m3u8_url = traverse_obj(program, ('streaming_url', {url_or_none}))
        if not m3u8_url:
            self.raise_login_required(
                'This program is only available for premium supporters')

        display_id = self._get_encoded_id(program)
        date_str = self._search_regex(
            rf'{program_id}0?(\d{{6}})', m3u8_url, 'date string', default=None)

        return {
            'display_id': display_id,
            'formats': self._extract_m3u8_formats(m3u8_url, raw_id, headers=self._HEADERS),
            'http_headers': self._HEADERS,
            'section_start': int_or_none(query.get('t', 0)),
            'upload_date': strftime_or_none(f'20{date_str}'),
            'webpage_url': f'{self._BASE_URL}/program/{program_id}?c={display_id}',
            **traverse_obj(program, {
                'id': ('id', {int}, {str_or_none}),
                'title': ('title', {clean_html}),
                'media_type': ('media_type', {str}),
                'thumbnail': ('poster_image_url', {url_or_none}, {update_url(query=None)}),
            }),
            **traverse_obj(programs, {
                'cast': (('performers', (*p_keys, 'guests')), ..., 'name', {str}, filter),
                'series_id': ('directory_name', {str}),
            }),
            **traverse_obj(programs, ('program_info', {
                'description': ('description', {clean_html}, filter),
                'series': ('title', {clean_html}),
                'tags': ('hashtag_list', ..., {str}, filter),
            })),
        }