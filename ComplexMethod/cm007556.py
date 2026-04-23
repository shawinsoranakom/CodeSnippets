def _real_extract(self, url):
        video_id = self._match_id(url)

        # Get video webpage for API data.
        webpage, handle = self._download_webpage_handle(
            'http://www.nicovideo.jp/watch/' + video_id, video_id)
        if video_id.startswith('so'):
            video_id = self._match_id(handle.geturl())

        api_data = self._parse_json(self._html_search_regex(
            'data-api-data="([^"]+)"', webpage,
            'API data', default='{}'), video_id)

        def get_video_info_web(items):
            return dict_get(api_data['video'], items)

        # Get video info
        video_info_xml = self._download_xml(
            'http://ext.nicovideo.jp/api/getthumbinfo/' + video_id,
            video_id, note='Downloading video info page')

        def get_video_info_xml(items):
            if not isinstance(items, list):
                items = [items]
            for item in items:
                ret = xpath_text(video_info_xml, './/' + item)
                if ret:
                    return ret

        if get_video_info_xml('error'):
            error_code = get_video_info_xml('code')

            if error_code == 'DELETED':
                raise ExtractorError('The video has been deleted.',
                                     expected=True)
            elif error_code == 'NOT_FOUND':
                raise ExtractorError('The video is not found.',
                                     expected=True)
            elif error_code == 'COMMUNITY':
                self.to_screen('%s: The video is community members only.' % video_id)
            else:
                raise ExtractorError('%s reports error: %s' % (self.IE_NAME, error_code))

        # Start extracting video formats
        formats = []

        # Get HTML5 videos info
        quality_info = try_get(api_data, lambda x: x['media']['delivery']['movie'])
        if not quality_info:
            raise ExtractorError('The video can\'t be downloaded', expected=True)

        for audio_quality in quality_info.get('audios') or {}:
            for video_quality in quality_info.get('videos') or {}:
                if not audio_quality.get('isAvailable') or not video_quality.get('isAvailable'):
                    continue
                formats.append(self._extract_format_for_quality(
                    api_data, video_id, audio_quality, video_quality))

        # Get flv/swf info
        timestamp = None
        video_real_url = try_get(api_data, lambda x: x['video']['smileInfo']['url'])
        if video_real_url:
            is_economy = video_real_url.endswith('low')

            if is_economy:
                self.report_warning('Site is currently in economy mode! You will only have access to lower quality streams')

            # Invoking ffprobe to determine resolution
            pp = FFmpegPostProcessor(self._downloader)
            cookies = self._get_cookies('https://nicovideo.jp').output(header='', sep='; path=/; domain=nicovideo.jp;\n')

            self.to_screen('%s: %s' % (video_id, 'Checking smile format with ffprobe'))

            try:
                metadata = pp.get_metadata_object(video_real_url, ['-cookies', cookies])
            except PostProcessingError as err:
                raise ExtractorError(err.msg, expected=True)

            v_stream = a_stream = {}

            # Some complex swf files doesn't have video stream (e.g. nm4809023)
            for stream in metadata['streams']:
                if stream['codec_type'] == 'video':
                    v_stream = stream
                elif stream['codec_type'] == 'audio':
                    a_stream = stream

            # Community restricted videos seem to have issues with the thumb API not returning anything at all
            filesize = int(
                (get_video_info_xml('size_high') if not is_economy else get_video_info_xml('size_low'))
                or metadata['format']['size']
            )
            extension = (
                get_video_info_xml('movie_type')
                or 'mp4' if 'mp4' in metadata['format']['format_name'] else metadata['format']['format_name']
            )

            # 'creation_time' tag on video stream of re-encoded SMILEVIDEO mp4 files are '1970-01-01T00:00:00.000000Z'.
            timestamp = (
                parse_iso8601(get_video_info_web('first_retrieve'))
                or unified_timestamp(get_video_info_web('postedDateTime'))
            )
            metadata_timestamp = (
                parse_iso8601(try_get(v_stream, lambda x: x['tags']['creation_time']))
                or timestamp if extension != 'mp4' else 0
            )

            # According to compconf, smile videos from pre-2017 are always better quality than their DMC counterparts
            smile_threshold_timestamp = parse_iso8601('2016-12-08T00:00:00+09:00')

            is_source = timestamp < smile_threshold_timestamp or metadata_timestamp > 0

            # If movie file size is unstable, old server movie is not source movie.
            if filesize > 1:
                formats.append({
                    'url': video_real_url,
                    'format_id': 'smile' if not is_economy else 'smile_low',
                    'format_note': 'SMILEVIDEO source' if not is_economy else 'SMILEVIDEO low quality',
                    'ext': extension,
                    'container': extension,
                    'vcodec': v_stream.get('codec_name'),
                    'acodec': a_stream.get('codec_name'),
                    # Some complex swf files doesn't have total bit rate metadata (e.g. nm6049209)
                    'tbr': int_or_none(metadata['format'].get('bit_rate'), scale=1000),
                    'vbr': int_or_none(v_stream.get('bit_rate'), scale=1000),
                    'abr': int_or_none(a_stream.get('bit_rate'), scale=1000),
                    'height': int_or_none(v_stream.get('height')),
                    'width': int_or_none(v_stream.get('width')),
                    'source_preference': 5 if not is_economy else -2,
                    'quality': 5 if is_source and not is_economy else None,
                    'filesize': filesize
                })

        self._sort_formats(formats)

        # Start extracting information
        title = (
            get_video_info_xml('title')  # prefer to get the untranslated original title
            or get_video_info_web(['originalTitle', 'title'])
            or self._og_search_title(webpage, default=None)
            or self._html_search_regex(
                r'<span[^>]+class="videoHeaderTitle"[^>]*>([^<]+)</span>',
                webpage, 'video title'))

        watch_api_data_string = self._html_search_regex(
            r'<div[^>]+id="watchAPIDataContainer"[^>]+>([^<]+)</div>',
            webpage, 'watch api data', default=None)
        watch_api_data = self._parse_json(watch_api_data_string, video_id) if watch_api_data_string else {}
        video_detail = watch_api_data.get('videoDetail', {})

        thumbnail = (
            self._html_search_regex(r'<meta property="og:image" content="([^"]+)">', webpage, 'thumbnail data', default=None)
            or dict_get(  # choose highest from 720p to 240p
                get_video_info_web('thumbnail'),
                ['ogp', 'player', 'largeUrl', 'middleUrl', 'url'])
            or self._html_search_meta('image', webpage, 'thumbnail', default=None)
            or video_detail.get('thumbnail'))

        description = get_video_info_web('description')

        if not timestamp:
            match = self._html_search_meta('datePublished', webpage, 'date published', default=None)
            if match:
                timestamp = parse_iso8601(match.replace('+', ':00+'))
        if not timestamp and video_detail.get('postedAt'):
            timestamp = parse_iso8601(
                video_detail['postedAt'].replace('/', '-'),
                delimiter=' ', timezone=datetime.timedelta(hours=9))
        timestamp = timestamp or try_get(api_data, lambda x: parse_iso8601(x['video']['registeredAt']))

        view_count = int_or_none(get_video_info_web(['view_counter', 'viewCount']))
        if not view_count:
            match = self._html_search_regex(
                r'>Views: <strong[^>]*>([^<]+)</strong>',
                webpage, 'view count', default=None)
            if match:
                view_count = int_or_none(match.replace(',', ''))
        view_count = (
            view_count
            or video_detail.get('viewCount')
            or try_get(api_data, lambda x: x['video']['count']['view']))

        comment_count = (
            int_or_none(get_video_info_web('comment_num'))
            or video_detail.get('commentCount')
            or try_get(api_data, lambda x: x['video']['count']['comment']))

        if not comment_count:
            match = self._html_search_regex(
                r'>Comments: <strong[^>]*>([^<]+)</strong>',
                webpage, 'comment count', default=None)
            if match:
                comment_count = int_or_none(match.replace(',', ''))

        duration = (parse_duration(
            get_video_info_web('length')
            or self._html_search_meta(
                'video:duration', webpage, 'video duration', default=None))
            or video_detail.get('length')
            or get_video_info_web('duration'))

        webpage_url = get_video_info_web('watch_url') or url

        # for channel movie and community movie
        channel_id = try_get(
            api_data,
            (lambda x: x['channel']['globalId'],
             lambda x: x['community']['globalId']))
        channel = try_get(
            api_data,
            (lambda x: x['channel']['name'],
             lambda x: x['community']['name']))

        # Note: cannot use api_data.get('owner', {}) because owner may be set to "null"
        # in the JSON, which will cause None to be returned instead of {}.
        owner = try_get(api_data, lambda x: x.get('owner'), dict) or {}
        uploader_id = str_or_none(
            get_video_info_web(['ch_id', 'user_id'])
            or owner.get('id')
            or channel_id
        )
        uploader = (
            get_video_info_web(['ch_name', 'user_nickname'])
            or owner.get('nickname')
            or channel
        )

        return {
            'id': video_id,
            '_api_data': api_data,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'uploader': uploader,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'channel': channel,
            'channel_id': channel_id,
            'view_count': view_count,
            'comment_count': comment_count,
            'duration': duration,
            'webpage_url': webpage_url,
        }