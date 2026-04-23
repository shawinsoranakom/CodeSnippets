def _real_extract(self, url):
        term, video_id = self._match_valid_url(url).group('term', 'id')
        frame = self._download_webpage(
            f'https://sejm-embed.redcdn.pl/Sejm{term}.nsf/VideoFrame.xsp/{video_id}',
            video_id)
        # despite it says "transmisje_arch", it works for live streams too!
        data = self._download_json(
            f'https://www.sejm.gov.pl/Sejm{term}.nsf/transmisje_arch.xsp/json/{video_id}',
            video_id)
        params = data['params']

        title = strip_or_none(data.get('title'))

        if data.get('status') == 'VIDEO_ENDED':
            live_status = 'was_live'
        elif data.get('status') == 'VIDEO_PLAYING':
            live_status = 'is_live'
        else:
            live_status = None
            self.report_warning(f'unknown status: {data.get("status")}')

        start_time = rfc3339_to_atende(params['start'])
        # current streams have a stop time of *expected* end of session, but actual times
        # can change during the transmission. setting a stop_time would artificially
        # end the stream at that time, while the session actually keeps going.
        if live_status == 'was_live':
            stop_time = rfc3339_to_atende(params['stop'])
            duration = (stop_time - start_time) // 1000
        else:
            stop_time, duration = None, None

        entries = []

        def add_entry(file, legacy_file=False):
            if not file:
                return
            file = self._proto_relative_url(file)
            if not legacy_file:
                file = update_url_query(file, {'startTime': start_time})
                if stop_time is not None:
                    file = update_url_query(file, {'stopTime': stop_time})
                stream_id = self._search_regex(r'/o2/sejm/([^/]+)/[^./]+\.livx', file, 'stream id')
            common_info = {
                'url': file,
                'duration': duration,
            }
            if legacy_file:
                entries.append({
                    **common_info,
                    'id': video_id,
                    'title': title,
                })
            else:
                entries.append({
                    **common_info,
                    '_type': 'url_transparent',
                    'ie_key': RedCDNLivxIE.ie_key(),
                    'id': stream_id,
                    'title': join_nonempty(title, stream_id, delim=' - '),
                })

        cameras = self._search_json(
            r'var\s+cameras\s*=', frame, 'camera list', video_id,
            contains_pattern=r'\[(?s:.+)\]', transform_source=js_to_json,
            fatal=False) or []
        for camera_file in traverse_obj(cameras, (..., 'file', {dict})):
            if camera_file.get('flv'):
                add_entry(camera_file['flv'])
            elif camera_file.get('mp4'):
                # this is only a thing in 7th term. no streams before, and starting 8th it's redcdn livx
                add_entry(camera_file['mp4'], legacy_file=True)
            else:
                self.report_warning('Unknown camera stream type found')

        if params.get('mig'):
            add_entry(self._search_regex(r"var sliUrl\s*=\s*'([^']+)'", frame, 'sign language interpreter url', fatal=False))

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': video_id,
            'title': title,
            'description': clean_html(data.get('desc')) or None,
            'duration': duration,
            'live_status': live_status,
            'location': strip_or_none(data.get('location')),
        }