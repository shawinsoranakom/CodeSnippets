def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        mobj = re.match(self._VALID_URL, url)
        resource_id = mobj.group('id')
        query = mobj.group('query')

        webpage, urlh = self._download_webpage_handle(url, resource_id)  # XXX: add UrlReferrer?
        redirect_url = urlh.geturl()

        # XXX: might have also extracted UrlReferrer and QueryString from the html
        service_path = compat_urlparse.urljoin(redirect_url, self._html_search_regex(
            r'<div[^>]+\bid=["\']ServicePath[^>]+>(.+?)</div>', webpage, resource_id,
            default='/Mediasite/PlayerService/PlayerService.svc/json'))

        player_options = self._download_json(
            '%s/GetPlayerOptions' % service_path, resource_id,
            headers={
                'Content-type': 'application/json; charset=utf-8',
                'X-Requested-With': 'XMLHttpRequest',
            },
            data=json.dumps({
                'getPlayerOptionsRequest': {
                    'ResourceId': resource_id,
                    'QueryString': query,
                    'UrlReferrer': data.get('UrlReferrer', ''),
                    'UseScreenReader': False,
                }
            }).encode('utf-8'))['d']

        presentation = player_options['Presentation']
        title = presentation['Title']

        if presentation is None:
            raise ExtractorError(
                'Mediasite says: %s' % player_options['PlayerPresentationStatusMessage'],
                expected=True)

        thumbnails = []
        formats = []
        for snum, Stream in enumerate(presentation['Streams']):
            stream_type = Stream.get('StreamType')
            if stream_type is None:
                continue

            video_urls = Stream.get('VideoUrls')
            if not isinstance(video_urls, list):
                video_urls = []

            stream_id = self._STREAM_TYPES.get(
                stream_type, 'type%u' % stream_type)

            stream_formats = []
            for unum, VideoUrl in enumerate(video_urls):
                video_url = url_or_none(VideoUrl.get('Location'))
                if not video_url:
                    continue
                # XXX: if Stream.get('CanChangeScheme', False), switch scheme to HTTP/HTTPS

                media_type = VideoUrl.get('MediaType')
                if media_type == 'SS':
                    stream_formats.extend(self._extract_ism_formats(
                        video_url, resource_id,
                        ism_id='%s-%u.%u' % (stream_id, snum, unum),
                        fatal=False))
                elif media_type == 'Dash':
                    stream_formats.extend(self._extract_mpd_formats(
                        video_url, resource_id,
                        mpd_id='%s-%u.%u' % (stream_id, snum, unum),
                        fatal=False))
                else:
                    stream_formats.append({
                        'format_id': '%s-%u.%u' % (stream_id, snum, unum),
                        'url': video_url,
                        'ext': mimetype2ext(VideoUrl.get('MimeType')),
                    })

            # TODO: if Stream['HasSlideContent']:
            # synthesise an MJPEG video stream '%s-%u.slides' % (stream_type, snum)
            # from Stream['Slides']
            # this will require writing a custom downloader...

            # disprefer 'secondary' streams
            if stream_type != 0:
                for fmt in stream_formats:
                    fmt['preference'] = -1

            thumbnail_url = Stream.get('ThumbnailUrl')
            if thumbnail_url:
                thumbnails.append({
                    'id': '%s-%u' % (stream_id, snum),
                    'url': urljoin(redirect_url, thumbnail_url),
                    'preference': -1 if stream_type != 0 else 0,
                })
            formats.extend(stream_formats)

        self._sort_formats(formats)

        # XXX: Presentation['Presenters']
        # XXX: Presentation['Transcript']

        return {
            'id': resource_id,
            'title': title,
            'description': presentation.get('Description'),
            'duration': float_or_none(presentation.get('Duration'), 1000),
            'timestamp': float_or_none(presentation.get('UnixTime'), 1000),
            'formats': formats,
            'thumbnails': thumbnails,
        }