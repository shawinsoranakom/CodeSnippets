def _real_extract(self, url):
        lang, video_id = self._match_valid_url(url).group('lang', 'id')
        metadata = self._download_metadata(url, video_id, lang, 'eventFallbackData')

        info = {
            'id': video_id,
            **traverse_obj(metadata, {
                'title': ('displayName', {str}),
                'description': ('description', {str}),
                'channel': ('labels', 'group', {str}),
                'location': ('labels', 'venue', {str}),
                'timestamp': ('startTime', {int_or_none}),
                'thumbnails': (('keyVisualUrl', 'alterKeyVisualUrl', 'heroKeyVisualUrl'), {'url': {url_or_none}}),
            }),
        }

        ended_time = traverse_obj(metadata, ('endedTime', {int_or_none}))
        if info.get('timestamp') and ended_time:
            info['duration'] = ended_time - info['timestamp']

        video_data, decrypt = self._call_encrypted_api(
            video_id, ':watchArchive', 'watch archive', data={'method': 1})
        # 'chromecastUrls' can be only partial videos, avoid
        info['formats'] = self._get_formats(video_data, ('hls', (('urls', ...), 'url'), {url_or_none}), video_id)
        for f in info['formats']:
            # bitrates are exaggerated in PPV playlists, so avoid wrong/huge filesize_approx values
            if f.get('tbr'):
                f['tbr'] = int(f['tbr'] / 2.5)
            # prefer variants with the same basename as the master playlist to avoid partial streams
            f['format_id'] = url_basename(f['url']).partition('.')[0]
            if not f['format_id'].startswith(url_basename(f['manifest_url']).partition('.')[0]):
                f['preference'] = -10

        hls_aes_key = traverse_obj(video_data, ('hls', 'key', {decrypt}))
        if hls_aes_key:
            info['hls_aes'] = {
                'key': hls_aes_key,
                'iv': traverse_obj(video_data, ('hls', 'iv', {decrypt})),
            }
        elif traverse_obj(video_data, ('hls', 'encryptType', {int})):
            self.report_warning('HLS AES-128 key was not found in API response')

        return info