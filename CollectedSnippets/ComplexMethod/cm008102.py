def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        if not video_id:
            webpage = self._download_webpage(url, display_id)
            video_id = self._html_search_regex(
                (r'<div[^>]+class=["\']player["\'][^>]+id=["\'](\d+)',
                 r'cloudId\s*=\s*["\'](\d+)',
                 r'class="video-preview current_playing" id="(\d+)"'),
                webpage, 'video id')

        video_data = self._download_json(
            f'http://cloud.tvigle.ru/api/play/video/{video_id}/', display_id)

        item = video_data['playlist']['items'][0]

        videos = item.get('videos')

        error_message = item.get('errorMessage')
        if not videos and error_message:
            if item.get('isGeoBlocked') is True:
                self.raise_geo_restricted(
                    msg=error_message, countries=self._GEO_COUNTRIES)
            else:
                raise ExtractorError(
                    f'{self.IE_NAME} returned error: {error_message}',
                    expected=True)

        title = item['title']
        description = item.get('description')
        thumbnail = item.get('thumbnail')
        duration = float_or_none(item.get('durationMilliseconds'), 1000)
        age_limit = parse_age_limit(item.get('ageRestrictions'))

        formats = []
        for vcodec, url_or_fmts in item['videos'].items():
            if vcodec == 'hls':
                m3u8_url = url_or_none(url_or_fmts)
                if not m3u8_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif vcodec == 'dash':
                mpd_url = url_or_none(url_or_fmts)
                if not mpd_url:
                    continue
                formats.extend(self._extract_mpd_formats(
                    mpd_url, video_id, mpd_id='dash', fatal=False))
            else:
                if not isinstance(url_or_fmts, dict):
                    continue
                for format_id, video_url in url_or_fmts.items():
                    if format_id == 'm3u8':
                        continue
                    video_url = url_or_none(video_url)
                    if not video_url:
                        continue
                    height = self._search_regex(
                        r'^(\d+)[pP]$', format_id, 'height', default=None)
                    filesize = int_or_none(try_get(
                        item, lambda x: x['video_files_size'][vcodec][format_id]))
                    formats.append({
                        'url': video_url,
                        'format_id': f'{vcodec}-{format_id}',
                        'vcodec': vcodec,
                        'height': int_or_none(height),
                        'filesize': filesize,
                    })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }