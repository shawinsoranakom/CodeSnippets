def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        bootstrap_data = self._search_regex(
            r'root\.DVR\.bootstrapData\s+=\s+"({.+?})";',
            webpage, 'bootstrap data')
        bootstrap_data = self._parse_json(
            bootstrap_data.encode('utf-8').decode('unicode_escape'),
            display_id)
        videos = self._parse_json(bootstrap_data['videos'], display_id)['allVideos']
        video_data = next(video for video in videos if video.get('slug') == display_id)

        series = video_data.get('showTitle')
        title = episode = video_data.get('title') or series
        if series and series != title:
            title = '%s - %s' % (series, title)

        formats = []
        for f, format_id in (('cdnUriM3U8', 'mobi'), ('webVideoUrlSd', 'sd'), ('webVideoUrlHd', 'hd')):
            f_url = video_data.get(f)
            if not f_url:
                continue
            formats.append({
                'format_id': format_id,
                'url': f_url,
            })

        return {
            'id': display_id,
            'display_id': display_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnail'),
            'duration': parse_duration(video_data.get('runTime')),
            'formats': formats,
            'episode': episode,
            'series': series,
        }