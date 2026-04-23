def _real_extract(self, url):
        video_id = self._match_id(url)

        movie_metadata = self._download_json(
            'https://rest.arbeitsagentur.de/infosysbub/berufetv/pc/v1/film-metadata',
            video_id, 'Downloading JSON metadata',
            headers={'X-API-Key': '79089773-4892-4386-86e6-e8503669f426'}, fatal=False)

        meta = traverse_obj(
            movie_metadata, ('metadaten', lambda _, i: video_id == i['miId']),
            get_all=False, default={})

        video = self._download_json(
            f'https://d.video-cdn.net/play/player/8YRzUk6pTzmBdrsLe9Y88W/video/{video_id}',
            video_id, 'Downloading video JSON')

        formats, subtitles = [], {}
        for key, source in video['videoSources']['html'].items():
            if key == 'auto':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(source[0]['source'], video_id)
                formats += fmts
                subtitles = subs
            else:
                formats.append({
                    'url': source[0]['source'],
                    'ext': mimetype2ext(source[0]['mimeType']),
                    'format_id': key,
                })

        for track in video.get('videoTracks') or []:
            if track.get('type') != 'SUBTITLES':
                continue
            subtitles.setdefault(track['language'], []).append({
                'url': track['source'],
                'name': track.get('label'),
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'title': meta.get('titel') or traverse_obj(video, ('videoMetaData', 'title')),
            'description': meta.get('beschreibung'),
            'thumbnail': meta.get('thumbnail') or f'https://asset-out-cdn.video-cdn.net/private/videos/{video_id}/thumbnails/active',
            'duration': float_or_none(video.get('duration'), scale=1000),
            'categories': [meta['kategorie']] if meta.get('kategorie') else None,
            'tags': meta.get('themengebiete'),
            'subtitles': subtitles,
            'formats': formats,
        }