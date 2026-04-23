def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        setup = self._parse_json(self._search_regex(
            r'setup\s*=\s*({.+});', webpage, 'setup'), video_id)
        player_setup = setup.get('player_setup') or setup
        video_data = player_setup.get('video') or {}
        formatted_metadata = video_data.get('formatted_metadata') or {}
        info = {
            'id': video_id,
            'title': player_setup.get('title') or video_data.get('title_short'),
            'description': video_data.get('description_long') or video_data.get('description_short'),
            'thumbnail': formatted_metadata.get('thumbnail') or video_data.get('brightcove_thumbnail'),
            'timestamp': unified_timestamp(formatted_metadata.get('video_publish_date')),
        }
        asset = try_get(setup, lambda x: x['embed_assets']['chorus'], dict) or {}

        formats = []
        hls_url = asset.get('hls_url')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
        mp4_url = asset.get('mp4_url')
        if mp4_url:
            tbr = self._search_regex(r'-(\d+)k\.', mp4_url, 'bitrate', default=None)
            format_id = 'http'
            if tbr:
                format_id += '-' + tbr
            formats.append({
                'format_id': format_id,
                'url': mp4_url,
                'tbr': int_or_none(tbr),
            })
        if formats:
            self._sort_formats(formats)
            info['formats'] = formats
            info['duration'] = int_or_none(asset.get('duration'))
            return info

        for provider_video_type in ('ooyala', 'youtube', 'brightcove'):
            provider_video_id = video_data.get('%s_id' % provider_video_type)
            if not provider_video_id:
                continue
            if provider_video_type == 'brightcove':
                info['formats'] = self._extract_once_formats(provider_video_id)
                self._sort_formats(info['formats'])
            else:
                info.update({
                    '_type': 'url_transparent',
                    'url': provider_video_id if provider_video_type == 'youtube' else '%s:%s' % (provider_video_type, provider_video_id),
                    'ie_key': provider_video_type.capitalize(),
                })
            return info
        raise ExtractorError('Unable to find provider video id')