def _extract_from_media_api(self, media_id):
        attributes = traverse_obj(
            self._call_api(f'media/{media_id}', media_id, fatal=False),
            ('data', 'attributes', {dict}))
        if not attributes:
            return None

        info_dict = traverse_obj(attributes, {
            'title': ('file_name', {lambda x: x.rpartition('.')[0]}),
            'timestamp': ('created_at', {parse_iso8601}),
            'duration': ('display', 'duration', {float_or_none}),
        })
        info_dict['id'] = media_id

        playback_url = traverse_obj(
            attributes, ('display', (None, 'viewer_playback_data'), 'url', {url_or_none}, any))
        download_url = traverse_obj(attributes, ('download_url', {url_or_none}))

        if playback_url and mimetype2ext(attributes.get('mimetype')) == 'm3u8':
            info_dict['formats'], info_dict['subtitles'] = self._extract_m3u8_formats_and_subtitles(
                playback_url, media_id, 'mp4', fatal=False, headers=self._HTTP_HEADERS)
            for f in info_dict['formats']:
                f['http_headers'] = self._HTTP_HEADERS
            if transcript_url := traverse_obj(attributes, ('display', 'transcript_url', {url_or_none})):
                info_dict['subtitles'].setdefault('en', []).append({
                    'url': transcript_url,
                    'ext': 'vtt',
                })
        elif playback_url or download_url:
            info_dict['formats'] = [{
                # If playback_url is available, download_url is a duplicate lower resolution format
                'url': playback_url or download_url,
                'vcodec': 'none' if attributes.get('media_type') != 'video' else None,
            }]

        if not info_dict.get('formats'):
            return None

        return info_dict