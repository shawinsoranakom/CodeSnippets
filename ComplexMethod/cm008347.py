def _real_extract(self, url):
        qs = parse_qs(url)

        author = qs.get('author', [None])[0]
        name = qs.get('name', [None])[0]
        clip_idx = qs.get('clip', [None])[0]
        course_name = qs.get('course', [None])[0]

        if any(not f for f in (author, name, clip_idx, course_name)):
            raise ExtractorError('Invalid URL', expected=True)

        display_id = f'{name}-{clip_idx}'

        course = self._download_course(course_name, url, display_id)

        collection = course['modules']

        clip = None

        for module_ in collection:
            if name in (module_.get('moduleName'), module_.get('name')):
                for clip_ in module_.get('clips', []):
                    clip_index = clip_.get('clipIndex')
                    if clip_index is None:
                        clip_index = clip_.get('index')
                    if clip_index is None:
                        continue
                    if str(clip_index) == clip_idx:
                        clip = clip_
                        break

        if not clip:
            raise ExtractorError('Unable to resolve clip')

        title = clip['title']
        clip_id = clip.get('clipName') or clip.get('name') or clip['clipId']

        QUALITIES = {
            'low': {'width': 640, 'height': 480},
            'medium': {'width': 848, 'height': 640},
            'high': {'width': 1024, 'height': 768},
            'high-widescreen': {'width': 1280, 'height': 720},
        }

        QUALITIES_PREFERENCE = ('low', 'medium', 'high', 'high-widescreen')
        quality_key = qualities(QUALITIES_PREFERENCE)

        AllowedQuality = collections.namedtuple('AllowedQuality', ['ext', 'qualities'])

        ALLOWED_QUALITIES = (
            AllowedQuality('webm', ['high']),
            AllowedQuality('mp4', ['low', 'medium', 'high']),
        )

        # Some courses also offer widescreen resolution for high quality (see
        # https://github.com/ytdl-org/youtube-dl/issues/7766)
        widescreen = course.get('supportsWideScreenVideoFormats') is True
        best_quality = 'high-widescreen' if widescreen else 'high'
        if widescreen:
            for allowed_quality in ALLOWED_QUALITIES:
                allowed_quality.qualities.append(best_quality)

        # In order to minimize the number of calls to ViewClip API and reduce
        # the probability of being throttled or banned by Pluralsight we will request
        # only single format until formats listing was explicitly requested.
        if self.get_param('listformats', False):
            allowed_qualities = ALLOWED_QUALITIES
        else:
            def guess_allowed_qualities():
                req_format = self.get_param('format') or 'best'
                req_format_split = req_format.split('-', 1)
                if len(req_format_split) > 1:
                    req_ext, req_quality = req_format_split
                    req_quality = '-'.join(req_quality.split('-')[:2])
                    for allowed_quality in ALLOWED_QUALITIES:
                        if req_ext == allowed_quality.ext and req_quality in allowed_quality.qualities:
                            return (AllowedQuality(req_ext, (req_quality, )), )
                req_ext = 'webm' if self.get_param('prefer_free_formats') else 'mp4'
                return (AllowedQuality(req_ext, (best_quality, )), )
            allowed_qualities = guess_allowed_qualities()

        formats = []
        for ext, qualities_ in allowed_qualities:
            for quality in qualities_:
                f = QUALITIES[quality].copy()
                clip_post = {
                    'author': author,
                    'includeCaptions': 'false',
                    'clipIndex': int(clip_idx),
                    'courseName': course_name,
                    'locale': 'en',
                    'moduleName': name,
                    'mediaType': ext,
                    'quality': '%dx%d' % (f['width'], f['height']),
                }
                format_id = f'{ext}-{quality}'

                try:
                    viewclip = self._download_json(
                        self._GRAPHQL_EP, display_id,
                        f'Downloading {format_id} viewclip graphql',
                        data=json.dumps({
                            'query': self.GRAPHQL_VIEWCLIP_TMPL % clip_post,
                            'variables': {},
                        }).encode(),
                        headers=self._GRAPHQL_HEADERS)['data']['viewClip']
                except ExtractorError:
                    # Still works but most likely will go soon
                    viewclip = self._download_json(
                        f'{self._API_BASE}/video/clips/viewclip', display_id,
                        f'Downloading {format_id} viewclip JSON', fatal=False,
                        data=json.dumps(clip_post).encode(),
                        headers={'Content-Type': 'application/json;charset=utf-8'})

                # Pluralsight tracks multiple sequential calls to ViewClip API and start
                # to return 429 HTTP errors after some time (see
                # https://github.com/ytdl-org/youtube-dl/pull/6989). Moreover it may even lead
                # to account ban (see https://github.com/ytdl-org/youtube-dl/issues/6842).
                # To somewhat reduce the probability of these consequences
                # we will sleep random amount of time before each call to ViewClip.
                self._sleep(
                    random.randint(5, 10), display_id,
                    '%(video_id)s: Waiting for %(timeout)s seconds to avoid throttling')

                if not viewclip:
                    continue

                clip_urls = viewclip.get('urls')
                if not isinstance(clip_urls, list):
                    continue

                for clip_url_data in clip_urls:
                    clip_url = clip_url_data.get('url')
                    if not clip_url:
                        continue
                    cdn = clip_url_data.get('cdn')
                    clip_f = f.copy()
                    clip_f.update({
                        'url': clip_url,
                        'ext': ext,
                        'format_id': f'{format_id}-{cdn}' if cdn else format_id,
                        'quality': quality_key(quality),
                        'source_preference': int_or_none(clip_url_data.get('rank')),
                    })
                    formats.append(clip_f)

        duration = int_or_none(
            clip.get('duration')) or parse_duration(clip.get('formattedDuration'))

        # TODO: other languages?
        subtitles = self.extract_subtitles(
            author, clip_idx, clip.get('clipId'), 'en', name, duration, display_id)

        return {
            'id': clip_id,
            'title': title,
            'duration': duration,
            'creator': author,
            'formats': formats,
            'subtitles': subtitles,
        }