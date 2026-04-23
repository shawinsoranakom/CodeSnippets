def _real_extract(self, url):
        display_id = self._match_id(url)
        if display_id.startswith('@'):
            display_id = display_id.replace(':', '#')
        else:
            display_id = display_id.replace('/', ':')
        display_id = urllib.parse.unquote(display_id)
        uri = 'lbry://' + display_id
        result = self._resolve_url(uri, display_id, 'stream')
        headers = {'Referer': 'https://odysee.com/'}

        formats = []
        stream_type = traverse_obj(result, ('value', 'stream_type', {str}))

        if stream_type in self._SUPPORTED_STREAM_TYPES:
            claim_id, is_live = result['claim_id'], False
            streaming_url = self._call_api_proxy(
                'get', claim_id, {
                    'uri': uri,
                    **traverse_obj(parse_qs(url), {
                        'signature': ('signature', 0),
                        'signature_ts': ('signature_ts', 0),
                    }),
                }, 'streaming url')['streaming_url']

            # GET request to v3 API returns original video/audio file if available
            direct_url = re.sub(r'/api/v\d+/', '/api/v3/', streaming_url)
            urlh = self._request_webpage(
                direct_url, display_id, 'Checking for original quality', headers=headers, fatal=False)
            if urlh and urlhandle_detect_ext(urlh) != 'm3u8':
                formats.append({
                    'url': direct_url,
                    'format_id': 'original',
                    'quality': 1,
                    **traverse_obj(result, ('value', {
                        'ext': ('source', (('name', {determine_ext}), ('media_type', {mimetype2ext}))),
                        'filesize': ('source', 'size', {int_or_none}),
                        'width': ('video', 'width', {int_or_none}),
                        'height': ('video', 'height', {int_or_none}),
                    }), get_all=False),
                    'vcodec': 'none' if stream_type == 'audio' else None,
                })

            final_url = None
            # HEAD request returns redirect response to m3u8 URL if available
            urlh = self._request_webpage(
                HEADRequest(streaming_url), display_id, headers=headers,
                note='Downloading streaming redirect url info', fatal=False)
            if urlh:
                final_url = urlh.url

        elif result.get('value_type') == 'stream' and stream_type not in self._UNSUPPORTED_STREAM_TYPES:
            claim_id, is_live = result['signing_channel']['claim_id'], True
            live_data = self._download_json(
                'https://api.odysee.live/livestream/is_live', claim_id,
                query={'channel_claim_id': claim_id},
                note='Downloading livestream JSON metadata')['data']
            final_url = live_data.get('VideoURL')
            # Upcoming videos may still give VideoURL
            if not live_data.get('Live'):
                final_url = None
                self.raise_no_formats('This stream is not live', True, claim_id)

        else:
            raise UnsupportedError(url)

        if determine_ext(final_url) == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                final_url, display_id, 'mp4', m3u8_id='hls', live=is_live, headers=headers))

        return {
            **self._parse_stream(result, url),
            'id': claim_id,
            'formats': formats,
            'is_live': is_live,
            'http_headers': headers,
        }