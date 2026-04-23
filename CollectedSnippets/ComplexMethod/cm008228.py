def _real_extract(self, url):
        video_id = self._match_id(url)
        try:
            self._start_session(video_id)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                self._login(video_id)
                self._start_session(video_id)
            else:
                raise

        metadata = self._download_json(f'https://api.onepeloton.com/api/ride/{video_id}/details?stream_source=multichannel', video_id)
        ride_data = metadata.get('ride')
        if not ride_data:
            raise ExtractorError('Missing stream metadata')
        token = self._get_token(video_id)

        is_live = False
        if ride_data.get('content_format') == 'audio':
            url = self._MANIFEST_URL_TEMPLATE % (ride_data.get('vod_stream_url'), urllib.parse.quote(token))
            formats = [{
                'url': url,
                'ext': 'm4a',
                'format_id': 'audio',
                'vcodec': 'none',
            }]
            subtitles = {}
        else:
            if ride_data.get('vod_stream_url'):
                url = 'https://members.onepeloton.com/.netlify/functions/m3u8-proxy?displayLanguage=en&acceptedSubtitles={}&url={}?hdnea={}'.format(
                    ','.join([re.sub('^([a-z]+)-([A-Z]+)$', r'\1', caption) for caption in ride_data['captions']]),
                    ride_data['vod_stream_url'],
                    urllib.parse.quote(urllib.parse.quote(token)))
            elif ride_data.get('live_stream_url'):
                url = self._MANIFEST_URL_TEMPLATE % (ride_data.get('live_stream_url'), urllib.parse.quote(token))
                is_live = True
            else:
                raise ExtractorError('Missing video URL')
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(url, video_id, 'mp4')

        if metadata.get('instructor_cues'):
            subtitles['cues'] = [{
                'data': json.dumps(metadata.get('instructor_cues')),
                'ext': 'json',
            }]

        category = ride_data.get('fitness_discipline_display_name')
        chapters = [{
            'start_time': segment.get('start_time_offset'),
            'end_time': segment.get('start_time_offset') + segment.get('length'),
            'title': segment.get('name'),
        } for segment in traverse_obj(metadata, ('segments', 'segment_list'))]

        return {
            'id': video_id,
            'title': ride_data.get('title'),
            'formats': formats,
            'thumbnail': url_or_none(ride_data.get('image_url')),
            'description': str_or_none(ride_data.get('description')),
            'creator': traverse_obj(ride_data, ('instructor', 'name')),
            'release_timestamp': ride_data.get('original_air_time'),
            'timestamp': ride_data.get('original_air_time'),
            'subtitles': subtitles,
            'duration': float_or_none(ride_data.get('length')),
            'categories': [category] if category else None,
            'tags': traverse_obj(ride_data, ('equipment_tags', ..., 'name')),
            'is_live': is_live,
            'chapters': chapters,
        }