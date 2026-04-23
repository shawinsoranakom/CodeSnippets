def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = compat_parse_qs(self._download_webpage(
            'https://drive.google.com/get_video_info',
            video_id, query={'docid': video_id}))

        def get_value(key):
            return try_get(video_info, lambda x: x[key][0])

        reason = get_value('reason')
        title = get_value('title')
        if not title and reason:
            raise ExtractorError(reason, expected=True)

        formats = []
        fmt_stream_map = (get_value('fmt_stream_map') or '').split(',')
        fmt_list = (get_value('fmt_list') or '').split(',')
        if fmt_stream_map and fmt_list:
            resolutions = {}
            for fmt in fmt_list:
                mobj = re.search(
                    r'^(?P<format_id>\d+)/(?P<width>\d+)[xX](?P<height>\d+)', fmt)
                if mobj:
                    resolutions[mobj.group('format_id')] = (
                        int(mobj.group('width')), int(mobj.group('height')))

            for fmt_stream in fmt_stream_map:
                fmt_stream_split = fmt_stream.split('|')
                if len(fmt_stream_split) < 2:
                    continue
                format_id, format_url = fmt_stream_split[:2]
                f = {
                    'url': lowercase_escape(format_url),
                    'format_id': format_id,
                    'ext': self._FORMATS_EXT[format_id],
                }
                resolution = resolutions.get(format_id)
                if resolution:
                    f.update({
                        'width': resolution[0],
                        'height': resolution[1],
                    })
                formats.append(f)

        source_url = update_url_query(
            'https://drive.google.com/uc', {
                'id': video_id,
                'export': 'download',
            })

        def request_source_file(source_url, kind):
            return self._request_webpage(
                source_url, video_id, note='Requesting %s file' % kind,
                errnote='Unable to request %s file' % kind, fatal=False)
        urlh = request_source_file(source_url, 'source')
        if urlh:
            def add_source_format(urlh):
                formats.append({
                    # Use redirect URLs as download URLs in order to calculate
                    # correct cookies in _calc_cookies.
                    # Using original URLs may result in redirect loop due to
                    # google.com's cookies mistakenly used for googleusercontent.com
                    # redirect URLs (see #23919).
                    'url': urlh.geturl(),
                    'ext': determine_ext(title, 'mp4').lower(),
                    'format_id': 'source',
                    'quality': 1,
                })
            if urlh.headers.get('Content-Disposition'):
                add_source_format(urlh)
            else:
                confirmation_webpage = self._webpage_read_content(
                    urlh, url, video_id, note='Downloading confirmation page',
                    errnote='Unable to confirm download', fatal=False)
                if confirmation_webpage:
                    confirm = self._search_regex(
                        r'confirm=([^&"\']+)', confirmation_webpage,
                        'confirmation code', default=None)
                    if confirm:
                        confirmed_source_url = update_url_query(source_url, {
                            'confirm': confirm,
                        })
                        urlh = request_source_file(confirmed_source_url, 'confirmed source')
                        if urlh and urlh.headers.get('Content-Disposition'):
                            add_source_format(urlh)
                    else:
                        self.report_warning(
                            get_element_by_class('uc-error-subcaption', confirmation_webpage)
                            or get_element_by_class('uc-error-caption', confirmation_webpage)
                            or 'unable to extract confirmation code')

        if not formats and reason:
            raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        hl = get_value('hl')
        subtitles_id = None
        ttsurl = get_value('ttsurl')
        if ttsurl:
            # the video Id for subtitles will be the last value in the ttsurl
            # query string
            subtitles_id = ttsurl.encode('utf-8').decode(
                'unicode_escape').split('=')[-1]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': 'https://drive.google.com/thumbnail?id=' + video_id,
            'duration': int_or_none(get_value('length_seconds')),
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, subtitles_id, hl),
            'automatic_captions': self.extract_automatic_captions(
                video_id, subtitles_id, hl),
        }