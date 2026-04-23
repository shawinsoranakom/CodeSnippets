def _extract_ngtv_info(self, media_id, tokenizer_query, software_statement, ap_data=None):
        if not isinstance(ap_data, dict):
            ap_data = {}
        is_live = ap_data.get('is_live')
        streams_data = self._download_json(
            f'https://medium.ngtv.io/media/{media_id}/tv',
            media_id)['media']['tv']
        duration = None
        chapters = []
        formats = []
        for supported_type in ('unprotected', 'bulkaes'):
            stream_data = streams_data.get(supported_type, {})
            m3u8_url = stream_data.get('secureUrl') or stream_data.get('url')
            if not m3u8_url:
                continue
            if stream_data.get('playlistProtection') == 'spe':
                m3u8_url = self._add_akamai_spe_token(
                    'https://token.ngtv.io/token/token_spe',
                    m3u8_url, media_id, ap_data, software_statement, tokenizer_query)
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, media_id, 'mp4', m3u8_id='hls', live=is_live, fatal=False))

            duration = float_or_none(stream_data.get('totalRuntime'))

            if not chapters and not is_live:
                for chapter in stream_data.get('contentSegments', []):
                    start_time = float_or_none(chapter.get('start'))
                    chapter_duration = float_or_none(chapter.get('duration'))
                    if start_time is None or chapter_duration is None:
                        continue
                    chapters.append({
                        'start_time': start_time,
                        'end_time': start_time + chapter_duration,
                    })

        if is_live:
            for f in formats:
                # Prevent ffmpeg from adding its own http headers or else we get HTTP Error 403
                f['downloader_options'] = {'ffmpeg_args': ['-seekable', '0', '-icy', '0']}

        return {
            'formats': formats,
            'chapters': chapters,
            'duration': duration,
        }