def _real_extract(self, url):
        url, _, headers = self._unsmuggle_headers(url)
        # XXX: Keep key name in sync with _unsmuggle_headers
        referrer = headers.get('Referer')
        event_id, unlisted_hash, video_id = self._match_valid_url(url).group('id', 'unlisted_hash', 'video_id')

        for retry in (False, True):
            try:
                live_event_data = self._call_events_api(
                    event_id, unlisted_hash=unlisted_hash, fields=self._EVENT_FIELDS,
                    referrer=referrer, query={'clip_to_play_id': video_id or '0'},
                    headers={'Accept': 'application/vnd.vimeo.*+json;version=3.4.9'})
                break
            except ExtractorError as e:
                if retry or not isinstance(e.cause, HTTPError) or e.cause.status not in (400, 403):
                    raise
                response = traverse_obj(e.cause.response.read(), ({json.loads}, {dict})) or {}
                error_code = response.get('error_code')
                if error_code == 2204:
                    self._verify_video_password(event_id, path='event')
                    continue
                if error_code == 3200:
                    raise ExtractorError(self._REFERER_HINT, expected=True)
                if error_msg := response.get('error'):
                    raise ExtractorError(f'Vimeo says: {error_msg}', expected=True)
                raise

        # stream_privacy.view can be: 'anybody', 'embed_only', 'nobody', 'password', 'unlisted'
        view_policy = live_event_data['stream_privacy']['view']
        if view_policy == 'nobody':
            raise ExtractorError('This event has not been made available to anyone', expected=True)

        clip_data = traverse_obj(live_event_data, ('clip_to_play', {dict})) or {}
        # live.status can be: 'streaming' (is_live), 'done' (was_live), 'unavailable' (is_upcoming OR dead)
        clip_status = traverse_obj(clip_data, ('live', 'status', {str}))
        start_time = traverse_obj(live_event_data, ('schedule', 'start_time', {str}))
        release_timestamp = parse_iso8601(start_time)

        if clip_status == 'unavailable' and release_timestamp and release_timestamp > time.time():
            self.raise_no_formats(f'This live event is scheduled for {start_time}', expected=True)
            live_status = 'is_upcoming'
            config_url = None

        elif view_policy == 'embed_only':
            webpage = self._download_webpage(
                join_nonempty('https://vimeo.com/event', event_id, 'embed', unlisted_hash, delim='/'),
                event_id, 'Downloading embed iframe webpage', impersonate=True, headers=headers)
            # The _parse_config result will overwrite live_status w/ 'is_live' if livestream is active
            live_status = 'was_live'
            config_url = self._extract_config_url(webpage)

        else:  # view_policy in ('anybody', 'password', 'unlisted')
            if video_id:
                clip_id, clip_hash = self._extract_video_id_and_unlisted_hash(clip_data)
                if video_id == clip_id and clip_status == 'done' and (clip_hash or view_policy != 'unlisted'):
                    return self._vimeo_url_result(clip_id, clip_hash, event_id)

                video_filter = lambda _, v: self._extract_video_id_and_unlisted_hash(v)[0] == video_id
            else:
                video_filter = lambda _, v: traverse_obj(v, ('live', 'status')) != 'unavailable'

            for page in itertools.count(1):
                videos_data = self._call_events_api(
                    event_id, 'videos', unlisted_hash=unlisted_hash, note=f'page {page}',
                    fields=self._VIDEOS_FIELDS, referrer=referrer, query={'page': page},
                    headers={'Accept': 'application/vnd.vimeo.*;version=3.4.1'})

                video = traverse_obj(videos_data, ('data', video_filter, any))
                if video or not traverse_obj(videos_data, ('paging', 'next', {str})):
                    break

            if not video:  # requested video_id is unavailable or no videos are available
                raise ExtractorError('This event video is unavailable', expected=True)

            live_status = {
                'streaming': 'is_live',
                'done': 'was_live',
                None: 'was_live',
            }.get(traverse_obj(video, ('live', 'status', {str})))

            if live_status == 'was_live':
                return self._vimeo_url_result(*self._extract_video_id_and_unlisted_hash(video), event_id)

            config_url = video['config_url']

        if config_url:  # view_policy == 'embed_only' or live_status == 'is_live'
            info = filter_dict(self._parse_config(
                self._download_json(config_url, event_id, 'Downloading config JSON'), event_id))
        else:  # live_status == 'is_upcoming'
            info = {'id': event_id}

        if info.get('live_status') == 'post_live':
            self.report_warning('This live event recently ended and some formats may not yet be available')

        return {
            **traverse_obj(live_event_data, {
                'title': ('title', {str}),
                'description': ('stream_description', {str}),
            }),
            'display_id': event_id,
            'live_status': live_status,
            'release_timestamp': release_timestamp,
            **info,
        }