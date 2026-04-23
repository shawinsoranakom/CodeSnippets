def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        course_id = mobj.group('course_id')

        query = {
            'videoId': video_id,
            'type': 'video',
        }

        video = self._download_json(
            'https://www.lynda.com/ajax/player', video_id,
            'Downloading video JSON', fatal=False, query=query)

        # Fallback scenario
        if not video:
            query['courseId'] = course_id

            play = self._download_json(
                'https://www.lynda.com/ajax/course/%s/%s/play'
                % (course_id, video_id), video_id, 'Downloading play JSON')

            if not play:
                self._raise_unavailable(video_id)

            formats = []
            for formats_dict in play:
                urls = formats_dict.get('urls')
                if not isinstance(urls, dict):
                    continue
                cdn = formats_dict.get('name')
                for format_id, format_url in urls.items():
                    if not format_url:
                        continue
                    formats.append({
                        'url': format_url,
                        'format_id': '%s-%s' % (cdn, format_id) if cdn else format_id,
                        'height': int_or_none(format_id),
                    })
            self._sort_formats(formats)

            conviva = self._download_json(
                'https://www.lynda.com/ajax/player/conviva', video_id,
                'Downloading conviva JSON', query=query)

            return {
                'id': video_id,
                'title': conviva['VideoTitle'],
                'description': conviva.get('VideoDescription'),
                'release_year': int_or_none(conviva.get('ReleaseYear')),
                'duration': int_or_none(conviva.get('Duration')),
                'creator': conviva.get('Author'),
                'formats': formats,
            }

        if 'Status' in video:
            raise ExtractorError(
                'lynda returned error: %s' % video['Message'], expected=True)

        if video.get('HasAccess') is False:
            self._raise_unavailable(video_id)

        video_id = compat_str(video.get('ID') or video_id)
        duration = int_or_none(video.get('DurationInSeconds'))
        title = video['Title']

        formats = []

        fmts = video.get('Formats')
        if fmts:
            formats.extend([{
                'url': f['Url'],
                'ext': f.get('Extension'),
                'width': int_or_none(f.get('Width')),
                'height': int_or_none(f.get('Height')),
                'filesize': int_or_none(f.get('FileSize')),
                'format_id': compat_str(f.get('Resolution')) if f.get('Resolution') else None,
            } for f in fmts if f.get('Url')])

        prioritized_streams = video.get('PrioritizedStreams')
        if prioritized_streams:
            for prioritized_stream_id, prioritized_stream in prioritized_streams.items():
                formats.extend([{
                    'url': video_url,
                    'height': int_or_none(format_id),
                    'format_id': '%s-%s' % (prioritized_stream_id, format_id),
                } for format_id, video_url in prioritized_stream.items()])

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        subtitles = self.extract_subtitles(video_id)

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'subtitles': subtitles,
            'formats': formats
        }