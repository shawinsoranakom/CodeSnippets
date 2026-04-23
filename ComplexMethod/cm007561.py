def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'https://play.tv2bornholm.dk/controls/AJAX.aspx/specifikVideo', video_id,
            data=json.dumps({
                'playlist_id': video_id,
                'serienavn': '',
            }).encode(), headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json; charset=UTF-8',
            })['d']

        # TODO: generalize flowplayer
        title = self._search_regex(
            r'title\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', video, 'title',
            group='value')
        sources = self._parse_json(self._search_regex(
            r'(?s)sources:\s*(\[.+?\]),', video, 'sources'),
            video_id, js_to_json)

        formats = []
        srcs = set()
        for source in sources:
            src = url_or_none(source.get('src'))
            if not src:
                continue
            if src in srcs:
                continue
            srcs.add(src)
            ext = determine_ext(src)
            src_type = source.get('type')
            if src_type == 'application/x-mpegurl' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif src_type == 'application/dash+xml' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    src, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'url': src,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }