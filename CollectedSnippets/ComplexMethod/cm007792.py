def _extract_video_info(self, video, stream, display_id):
        title = video['name']

        if not stream:
            if video.get('authenticated') is True:
                raise ExtractorError(
                    'This video is only available via cable service provider subscription that'
                    ' is not currently supported. You may want to use --cookies.', expected=True)
            else:
                raise ExtractorError('Unable to find stream')
        STREAM_URL_SUFFIX = 'streamUrl'
        formats = []
        for stream_kind in ('', 'hds'):
            suffix = STREAM_URL_SUFFIX.capitalize() if stream_kind else STREAM_URL_SUFFIX
            stream_url = stream.get('%s%s' % (stream_kind, suffix))
            if not stream_url:
                continue
            if stream_kind == '':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, display_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif stream_kind == 'hds':
                formats.extend(self._extract_f4m_formats(
                    stream_url, display_id, f4m_id=stream_kind, fatal=False))
        self._sort_formats(formats)

        video_id = video.get('id') or display_id
        description = video.get('description', {}).get('detailed')
        duration = int_or_none(video.get('duration'))

        series = video.get('show', {}).get('name')
        season_number = int_or_none(video.get('season', {}).get('number'))
        episode_number = int_or_none(video.get('episodeNumber'))

        tags = video.get('tags')
        age_limit = parse_age_limit(video.get('parental', {}).get('rating'))

        subtitles = {}
        captions = stream.get('captions')
        if isinstance(captions, list):
            for caption in captions:
                subtitle_url = url_or_none(caption.get('fileUrl'))
                if not subtitle_url or not subtitle_url.startswith('http'):
                    continue
                lang = caption.get('fileLang', 'en')
                ext = determine_ext(subtitle_url)
                subtitles.setdefault(lang, []).append({
                    'url': subtitle_url,
                    'ext': 'ttml' if ext == 'xml' else ext,
                })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'duration': duration,
            'series': series,
            'season_number': season_number,
            'episode_number': episode_number,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
            'subtitles': subtitles,
        }