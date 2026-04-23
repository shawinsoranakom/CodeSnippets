def _extract_ngtv_info(self, media_id, tokenizer_query, ap_data=None):
        streams_data = self._download_json(
            'http://medium.ngtv.io/media/%s/tv' % media_id,
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
                    'http://token.ngtv.io/token/token_spe',
                    m3u8_url, media_id, ap_data or {}, tokenizer_query)
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False))

            duration = float_or_none(stream_data.get('totalRuntime'))

            if not chapters:
                for chapter in stream_data.get('contentSegments', []):
                    start_time = float_or_none(chapter.get('start'))
                    chapter_duration = float_or_none(chapter.get('duration'))
                    if start_time is None or chapter_duration is None:
                        continue
                    chapters.append({
                        'start_time': start_time,
                        'end_time': start_time + chapter_duration,
                    })
        self._sort_formats(formats)

        return {
            'formats': formats,
            'chapters': chapters,
            'duration': duration,
        }