def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = (
            self._html_search_meta(
                ('ed_title', 'search.ed_title'), webpage, default=None)
            or self._search_regex(
                r'data-favorite_title_(?:eng|chi)=(["\'])(?P<id>(?:(?!\1).)+)\1',
                webpage, 'title', default=None, group='url')
            or self._html_search_regex(
                r'<h1>([^<]+)</h1>', webpage, 'title', default=None)
            or self._og_search_title(webpage)
        )

        file_id = self._search_regex(
            r'post_var\[["\']file_id["\']\s*\]\s*=\s*(.+?);',
            webpage, 'file ID')
        curr_url = self._search_regex(
            r'post_var\[["\']curr_url["\']\s*\]\s*=\s*"(.+?)";',
            webpage, 'curr URL')
        data = {
            'action': 'get_info',
            'curr_url': curr_url,
            'file_id': file_id,
            'video_url': file_id,
        }

        response = self._download_json(
            self._APPS_BASE_URL + '/media/play/handler.php', video_id,
            data=urlencode_postdata(data),
            headers=merge_dicts({
                'Content-Type': 'application/x-www-form-urlencoded'},
                self.geo_verification_headers()))

        result = response['result']

        if not response.get('success') or not response.get('access'):
            error = clean_html(response.get('access_err_msg'))
            if 'Video streaming is not available in your country' in error:
                self.raise_geo_restricted(
                    msg=error, countries=self._GEO_COUNTRIES)
            else:
                raise ExtractorError(error, expected=True)

        formats = []

        width = int_or_none(result.get('width'))
        height = int_or_none(result.get('height'))

        playlist0 = result['playlist'][0]
        for fmt in playlist0['sources']:
            file_url = urljoin(self._APPS_BASE_URL, fmt.get('file'))
            if not file_url:
                continue
            # If we ever wanted to provide the final resolved URL that
            # does not require cookies, albeit with a shorter lifespan:
            #     urlh = self._downloader.urlopen(file_url)
            #     resolved_url = urlh.geturl()
            label = fmt.get('label')
            h = self._FORMAT_HEIGHTS.get(label)
            w = h * width // height if h and width and height else None
            formats.append({
                'format_id': label,
                'ext': fmt.get('type'),
                'url': file_url,
                'width': w,
                'height': h,
            })
        self._sort_formats(formats)

        subtitles = {}
        tracks = try_get(playlist0, lambda x: x['tracks'], list) or []
        for track in tracks:
            if not isinstance(track, dict):
                continue
            track_kind = str_or_none(track.get('kind'))
            if not track_kind or not isinstance(track_kind, compat_str):
                continue
            if track_kind.lower() not in ('captions', 'subtitles'):
                continue
            track_url = urljoin(self._APPS_BASE_URL, track.get('file'))
            if not track_url:
                continue
            track_label = track.get('label')
            subtitles.setdefault(self._CC_LANGS.get(
                track_label, track_label), []).append({
                    'url': self._proto_relative_url(track_url),
                    'ext': 'srt',
                })

        # Likes
        emotion = self._download_json(
            'https://emocounter.hkedcity.net/handler.php', video_id,
            data=urlencode_postdata({
                'action': 'get_emotion',
                'data[bucket_id]': 'etv',
                'data[identifier]': video_id,
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            fatal=False) or {}
        like_count = int_or_none(try_get(
            emotion, lambda x: x['data']['emotion_data'][0]['count']))

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta(
                'description', webpage, fatal=False),
            'upload_date': unified_strdate(self._html_search_meta(
                'ed_date', webpage, fatal=False), day_first=False),
            'duration': int_or_none(result.get('length')),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': urljoin(self._APPS_BASE_URL, result.get('image')),
            'view_count': parse_count(result.get('view_count')),
            'like_count': like_count,
        }