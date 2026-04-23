def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._call_api('videos/{0}.json'.format(video_id), video_id, 'Downloading video JSON', query={})

        self._check_errors(video)

        title = try_get(video, lambda x: x['titles']['en'], str)
        episode_number = int_or_none(video.get('number'))
        if not title:
            title = 'Episode %d' % episode_number if video.get('type') == 'episode' else video.get('id') or video_id
            container_titles = try_get(video, lambda x: x['container']['titles'], dict) or {}
            container_title = self.dict_selection(container_titles, 'en')
            if container_title and title == video_id:
                title = container_title
            else:
                title = '%s - %s' % (container_title, title)

        resp = self._call_api(
            'playback_streams/%s.json?drms=dt3&device_id=%s' % (video_id, self._DEVICE_ID),
            video_id, 'Downloading video streams JSON')['main'][0]

        mpd_url = resp['url']
        # 720p is hidden in another MPD which can be found in the current manifest content
        mpd_content = self._download_webpage(mpd_url, video_id, note='Downloading initial MPD manifest')
        mpd_url = self._search_regex(
            r'(?mi)<BaseURL>(http.+.mpd)', mpd_content, 'new manifest', default=mpd_url)
        if 'mpdhd_high' not in mpd_url:
            # Modify the URL to get 1080p
            mpd_url = mpd_url.replace('mpdhd', 'mpdhd_high')
        formats = self._extract_mpd_formats(mpd_url, video_id)
        self._sort_formats(formats)

        description = self.dict_selection(video.get('descriptions', {}), 'en')
        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail['url'],
        } for thumbnail_id, thumbnail in (video.get('images') or {}).items() if thumbnail.get('url')]
        like_count = int_or_none(try_get(video, lambda x: x['likes']['count']))

        stream_id = try_get(resp, lambda x: x['properties']['track']['stream_id'])
        subtitles = dict((lang, [{
            'ext': ext,
            'url': self._API_URL_TEMPLATE % self._api_query(
                'videos/{0}/auth_subtitles/{1}.{2}'.format(video_id, lang, ext), stream_id=stream_id)
        } for ext in ('srt', 'vtt')]) for lang in (video.get('subtitle_completions') or {}).keys())

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'duration': int_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('created_at')),
            'uploader': video.get('author'),
            'uploader_url': video.get('author_url'),
            'like_count': like_count,
            'age_limit': parse_age_limit(video.get('rating')),
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'episode_number': episode_number,
        }