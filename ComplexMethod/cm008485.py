def _real_extract(self, url):
        user_id, video_id = self._match_valid_url(url).group('user_id', 'id')
        query = {
            'contentId': f'{user_id}-vod-{video_id}',
            'provider': 'universe',
            **traverse_obj(url, ({parse_qs}, 'uss_token', {'signedKey': -1})),
        }
        info = self._download_json(self._API_INFO_URL, video_id, query=query, fatal=False)
        access = self._download_json(
            'https://playback.dacast.com/content/access', video_id,
            note='Downloading access JSON', query=query, expected_status=403)

        error = access.get('error')
        if error in ('Broadcaster has been blocked', 'Content is offline'):
            raise ExtractorError(error, expected=True)
        elif error:
            raise ExtractorError(f'Dacast API says "{error}"')

        hls_url = access['hls']
        hls_aes = {}

        if 'DRM_EXT' in hls_url:
            self.report_drm(video_id)
        elif '/uspaes/' in hls_url:
            # Ref: https://player.dacast.com/js/player.js
            ts = int(time.time())
            signature = hashlib.sha1(
                f'{10413792000 - ts}{ts}{self._usp_signing_secret}'.encode()).digest().hex()
            hls_aes['uri'] = f'https://keys.dacast.com/uspaes/{video_id}.key?s={signature}&ts={ts}'

        for retry in self.RetryManager():
            try:
                formats = self._extract_m3u8_formats(hls_url, video_id, 'mp4', m3u8_id='hls')
            except ExtractorError as e:
                # CDN will randomly respond with 403
                if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    retry.error = e
                    continue
                raise

        return {
            'id': video_id,
            'uploader_id': user_id,
            'formats': formats,
            'hls_aes': hls_aes or None,
            **traverse_obj(info, ('contentInfo', {
                'title': 'title',
                'duration': ('duration', {float_or_none}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
            })),
        }