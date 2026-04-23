def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data = self._search_nextjs_data(webpage, video_id)['props']['initialState']
        video_data = try_get(data, lambda x: x['video']['current'], dict)
        if not video_data:
            video_data = data['article']['content'][0]['primaryMedia']['video']
        title = video_data['headline']['primary']

        formats = []
        for va in video_data.get('videoAssets', []):
            public_url = va.get('publicUrl')
            if not public_url:
                continue
            if '://link.theplatform.com/' in public_url:
                public_url = update_url_query(public_url, {'format': 'redirect'})
            format_id = va.get('format')
            if format_id == 'M3U':
                formats.extend(self._extract_m3u8_formats(
                    public_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False))
                continue
            tbr = int_or_none(va.get('bitrate'), 1000)
            formats.append({
                'format_id': join_nonempty(format_id, tbr),
                'url': public_url,
                'width': int_or_none(va.get('width')),
                'height': int_or_none(va.get('height')),
                'tbr': tbr,
                'ext': 'mp4',
            })

        subtitles = {}
        closed_captioning = video_data.get('closedCaptioning')
        if closed_captioning:
            for cc_url in closed_captioning.values():
                if not cc_url:
                    continue
                subtitles.setdefault('en', []).append({
                    'url': cc_url,
                })

        return {
            'id': video_id,
            'title': title,
            'description': try_get(video_data, lambda x: x['description']['primary']),
            'thumbnail': try_get(video_data, lambda x: x['primaryImage']['url']['primary']),
            'duration': parse_duration(video_data.get('duration')),
            'timestamp': unified_timestamp(video_data.get('datePublished')),
            'formats': formats,
            'subtitles': subtitles,
        }