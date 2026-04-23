def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = self._download_json(
            f'https://content-workspacevideo-pa.googleapis.com/v1/drive/media/{video_id}/playback',
            video_id, 'Downloading video webpage', query={'key': 'AIzaSyDVQw45DwoYh632gvsP5vPDqEKvb-Ywnb8'},
            headers={'Referer': 'https://drive.google.com/'})

        formats = []
        for fmt in traverse_obj(video_info, (
                'mediaStreamingData', 'formatStreamingData', ('adaptiveTranscodes', 'progressiveTranscodes'),
                lambda _, v: url_or_none(v['url']))):
            formats.append({
                **traverse_obj(fmt, {
                    'url': 'url',
                    'format_id': ('itag', {int}, {str_or_none}),
                }),
                **traverse_obj(fmt, ('transcodeMetadata', {
                    'ext': ('mimeType', {mimetype2ext}),
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'fps': ('videoFps', {int_or_none}),
                    'filesize': ('contentLength', {int_or_none}),
                    'vcodec': ((('videoCodecString', {str}), {value('none')}), any),
                    'acodec': ((('audioCodecString', {str}), {value('none')}), any),
                })),
                'downloader_options': {
                    'http_chunk_size': 10 << 20,
                },
            })

        title = traverse_obj(video_info, ('mediaMetadata', 'title', {str}))

        source_url = update_url_query(
            'https://drive.usercontent.google.com/download', {
                'id': video_id,
                'export': 'download',
                'confirm': 't',
            })

        def request_source_file(source_url, kind, data=None):
            return self._request_webpage(
                source_url, video_id, note=f'Requesting {kind} file',
                errnote=f'Unable to request {kind} file', fatal=False, data=data)
        urlh = request_source_file(source_url, 'source')
        if urlh:
            def add_source_format(urlh):
                nonlocal title
                if not title:
                    title = self._search_regex(
                        r'\bfilename="([^"]+)"', urlh.headers.get('Content-Disposition'),
                        'title', default=None)
                formats.append({
                    # Use redirect URLs as download URLs in order to calculate
                    # correct cookies in _calc_cookies.
                    # Using original URLs may result in redirect loop due to
                    # google.com's cookies mistakenly used for googleusercontent.com
                    # redirect URLs (see #23919).
                    'url': urlh.url,
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
                    confirmed_source_url = extract_attributes(
                        get_element_html_by_id('download-form', confirmation_webpage) or '').get('action')
                    if confirmed_source_url:
                        urlh = request_source_file(confirmed_source_url, 'confirmed source', data=b'')
                        if urlh and urlh.headers.get('Content-Disposition'):
                            add_source_format(urlh)
                    else:
                        self.report_warning(
                            get_element_by_class('uc-error-subcaption', confirmation_webpage)
                            or get_element_by_class('uc-error-caption', confirmation_webpage)
                            or 'unable to extract confirmation code')

        return {
            'id': video_id,
            'title': title,
            **traverse_obj(video_info, {
                'duration': ('mediaMetadata', 'duration', {parse_duration}),
                'thumbnails': ('thumbnails', lambda _, v: url_or_none(v['url']), {
                    'url': 'url',
                    'ext': ('mimeType', {mimetype2ext}),
                    'width': ('width', {int}),
                    'height': ('height', {int}),
                }),
            }),
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, video_info),
        }