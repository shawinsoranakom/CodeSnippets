def _real_extract(self, url):
        video_id = self._match_id(url)
        tk2 = base64.urlsafe_b64encode(
            f'did={uuid.uuid4()}|pno=1030|ver=0.3.0301|clit={int(time.time())}'.encode())[::-1]
        try:
            api_data = self._download_json(
                'https://pcweb.api.mgtv.com/player/video', video_id, query={
                    'tk2': tk2,
                    'video_id': video_id,
                    'type': 'pch5',
                }, headers=self.geo_verification_headers())['data']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                error = self._parse_json(e.cause.response.read().decode(), None)
                if error.get('code') == 40005:
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                raise ExtractorError(error['msg'], expected=True)
            raise

        stream_data = self._download_json(
            'https://pcweb.api.mgtv.com/player/getSource', video_id, query={
                'tk2': tk2,
                'pm2': api_data['atc']['pm2'],
                'video_id': video_id,
                'type': 'pch5',
                'src': 'intelmgtv',
            }, headers=self.geo_verification_headers())['data']
        stream_domain = traverse_obj(stream_data, ('stream_domain', ..., {url_or_none}), get_all=False)

        formats = []
        for idx, stream in enumerate(traverse_obj(stream_data, ('stream', lambda _, v: v['url']))):
            stream_name = traverse_obj(stream, 'name', 'standardName', 'barName', expected_type=str)
            resolution = traverse_obj(
                self._RESOLUTIONS, (stream_name, 1 if stream.get('scale') == '16:9' else 0))
            format_url = traverse_obj(self._download_json(
                urljoin(stream_domain, stream['url']), video_id, fatal=False,
                note=f'Downloading video info for format {resolution or stream_name}'),
                ('info', {url_or_none}))
            if not format_url:
                continue
            tbr = int_or_none(stream.get('filebitrate') or self._search_regex(
                r'_(\d+)_mp4/', format_url, 'tbr', default=None))
            formats.append({
                'format_id': str(tbr or idx),
                'url': format_url,
                'ext': 'mp4',
                'tbr': tbr,
                'vcodec': stream.get('videoFormat'),
                'acodec': stream.get('audioFormat'),
                **parse_resolution(resolution),
                'protocol': 'm3u8_native',
                'http_headers': {
                    'Referer': url,
                },
                'format_note': stream_name,
            })

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(api_data, ('info', {
                'title': ('title', {str.strip}),
                'description': ('desc', {str}),
                'duration': ('duration', {int_or_none}),
                'thumbnail': ('thumb', {url_or_none}),
            })),
            'subtitles': self.extract_subtitles(video_id, stream_domain),
        }