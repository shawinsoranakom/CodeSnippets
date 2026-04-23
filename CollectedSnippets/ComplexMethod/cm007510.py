def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://view.vzaar.com/v2/%s/video' % video_id, video_id)

        title = video_data.get('videoTitle') or video_id

        formats = []

        source_url = url_or_none(video_data.get('sourceUrl'))
        if source_url:
            f = {
                'url': source_url,
                'format_id': 'http',
                'preference': 1,
            }
            if 'audio' in source_url:
                f.update({
                    'vcodec': 'none',
                    'ext': 'mp3',
                })
            else:
                f.update({
                    'width': int_or_none(video_data.get('width')),
                    'height': int_or_none(video_data.get('height')),
                    'ext': 'mp4',
                    'fps': float_or_none(video_data.get('fps')),
                })
            formats.append(f)

        video_guid = video_data.get('guid')
        usp = video_data.get('usp')
        if video_data.get('uspEnabled') and isinstance(video_guid, compat_str) and isinstance(usp, dict):
            hls_aes = video_data.get('hlsAes')
            qs = '&'.join('%s=%s' % (k, v) for k, v in usp.items())
            url_templ = 'http://%%s.vzaar.com/v5/usp%s/%s/%s.ism%%s?' % ('aes' if hls_aes else '', video_guid, video_id)
            m3u8_formats = self._extract_m3u8_formats(
                url_templ % ('fable', '/.m3u8') + qs, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
            if hls_aes:
                for f in m3u8_formats:
                    f['_decryption_key_url'] = url_templ % ('goose', '') + qs
            formats.extend(m3u8_formats)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._proto_relative_url(video_data.get('poster')),
            'duration': float_or_none(video_data.get('videoDuration')),
            'timestamp': unified_timestamp(video_data.get('ts')),
            'formats': formats,
        }