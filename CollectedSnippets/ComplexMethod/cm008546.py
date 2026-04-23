def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        mobj = self._match_valid_url(url)
        resource_id = mobj.group('id')
        query = mobj.group('query')

        webpage, urlh = self._download_webpage_handle(url, resource_id)  # XXX: add UrlReferrer?
        redirect_url = urlh.url

        # XXX: might have also extracted UrlReferrer and QueryString from the html
        service_path = urllib.parse.urljoin(redirect_url, self._html_search_regex(
            r'<div[^>]+\bid=["\']ServicePath[^>]+>(.+?)</div>', webpage, resource_id,
            default='/Mediasite/PlayerService/PlayerService.svc/json'))

        player_options = self._download_json(
            f'{service_path}/GetPlayerOptions', resource_id,
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
                },
            }).encode())['d']

        presentation = player_options['Presentation']
        title = presentation['Title']

        if presentation is None:
            raise ExtractorError(
                'Mediasite says: {}'.format(player_options['PlayerPresentationStatusMessage']),
                expected=True)

        thumbnails = []
        formats = []
        for snum, stream in enumerate(presentation['Streams']):
            stream_type = stream.get('StreamType')
            if stream_type is None:
                continue

            video_urls = stream.get('VideoUrls')
            if not isinstance(video_urls, list):
                video_urls = []

            stream_id = self._STREAM_TYPES.get(
                stream_type, 'type%u' % stream_type)

            stream_formats = []
            for unum, video in enumerate(video_urls):
                video_url = url_or_none(video.get('Location'))
                if not video_url:
                    continue
                # XXX: if Stream.get('CanChangeScheme', False), switch scheme to HTTP/HTTPS

                media_type = video.get('MediaType')
                ext = mimetype2ext(video.get('MimeType'))
                if media_type == 'SS':
                    stream_formats.extend(self._extract_ism_formats(
                        video_url, resource_id,
                        ism_id=f'{stream_id}-{snum}.{unum}',
                        fatal=False))
                elif media_type == 'Dash':
                    stream_formats.extend(self._extract_mpd_formats(
                        video_url, resource_id,
                        mpd_id=f'{stream_id}-{snum}.{unum}',
                        fatal=False))
                elif ext in ('m3u', 'm3u8'):
                    stream_formats.extend(self._extract_m3u8_formats(
                        video_url, resource_id,
                        m3u8_id=f'{stream_id}-{snum}.{unum}',
                        fatal=False))
                else:
                    stream_formats.append({
                        'format_id': f'{stream_id}-{snum}.{unum}',
                        'url': video_url,
                        'ext': ext,
                    })

            images = traverse_obj(player_options, ('PlayerLayoutOptions', 'Images', {dict}))
            if stream.get('HasSlideContent') and images:
                stream_formats.append(self.__extract_slides(
                    stream_id=stream_id,
                    snum=snum,
                    stream=stream,
                    duration=presentation.get('Duration'),
                    images=images,
                ))

            # disprefer 'secondary' streams
            if stream_type != 0:
                for fmt in stream_formats:
                    fmt['quality'] = -10

            thumbnail_url = stream.get('ThumbnailUrl')
            if thumbnail_url:
                thumbnails.append({
                    'id': f'{stream_id}-{snum}',
                    'url': urljoin(redirect_url, thumbnail_url),
                    'preference': -1 if stream_type != 0 else 0,
                })
            formats.extend(stream_formats)

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