def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = f'http://embed.live.huffingtonpost.com/api/segments/{video_id}.json'
        data = self._download_json(api_url, video_id)['data']

        video_title = data['title']
        duration = parse_duration(data.get('running_time'))
        upload_date = unified_strdate(
            data.get('schedule', {}).get('starts_at') or data.get('segment_start_date_time'))
        description = data.get('description')

        thumbnails = []
        for url in filter(None, data['images'].values()):
            m = re.match(r'.*-([0-9]+x[0-9]+)\.', url)
            if not m:
                continue
            thumbnails.append({
                'url': url,
                'resolution': m.group(1),
            })

        formats = []
        sources = data.get('sources', {})
        live_sources = list(sources.get('live', {}).items()) + list(sources.get('live_again', {}).items())
        for key, url in live_sources:
            ext = determine_ext(url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    url, video_id, ext='mp4', m3u8_id='hls', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    url + '?hdcore=2.9.5', video_id, f4m_id='hds', fatal=False))
            else:
                formats.append({
                    'format': key,
                    'format_id': key.replace('/', '.'),
                    'ext': 'mp4',
                    'url': url,
                    'vcodec': 'none' if key.startswith('audio/') else None,
                })

        return {
            'id': video_id,
            'title': video_title,
            'description': description,
            'formats': formats,
            'duration': duration,
            'upload_date': upload_date,
            'thumbnails': thumbnails,
        }