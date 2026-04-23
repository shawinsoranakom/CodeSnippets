def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_api('media', video_id, fatal=False, expected_status=404)
        webpage = self._download_webpage(
            'https://i.imgur.com/{id}.gifv'.format(id=video_id), video_id, fatal=not data) or ''

        if not traverse_obj(data, ('media', 0, (
                ('type', T(lambda t: t == 'video' or None)),
                ('metadata', 'is_animated'))), get_all=False):
            raise ExtractorError(
                '%s is not a video or animated image' % video_id,
                expected=True)

        media_fmt = traverse_obj(data, ('media', 0, {
            'url': ('url', T(url_or_none)),
            'ext': 'ext',
            'width': ('width', T(int_or_none)),
            'height': ('height', T(int_or_none)),
            'filesize': ('size', T(int_or_none)),
            'acodec': ('metadata', 'has_sound', T(lambda b: None if b else 'none')),
        }))

        media_url = traverse_obj(media_fmt, 'url')
        if media_url:
            if not media_fmt.get('ext'):
                media_fmt['ext'] = mimetype2ext(traverse_obj(
                    data, ('media', 0, 'mime_type'))) or determine_ext(media_url)
            if traverse_obj(data, ('media', 0, 'type')) == 'image':
                media_fmt['acodec'] = 'none'
                media_fmt.setdefault('preference', -10)

        tw_formats = self._extract_twitter_formats(webpage)
        if traverse_obj(tw_formats, (0, 'url')) == media_url:
            tw_formats = []
        else:
            # maybe this isn't an animated image/video?
            self._check_formats(tw_formats, video_id)

        video_elements = self._search_regex(
            r'(?s)<div class="video-elements">(.*?)</div>',
            webpage, 'video elements', default=None)
        if not (video_elements or tw_formats or media_url):
            raise ExtractorError(
                'No sources found for video %s. Maybe a plain image?' % video_id,
                expected=True)

        def mung_format(fmt, *extra):
            fmt.update({
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })
            for d in extra:
                fmt.update(d)
            return fmt

        if video_elements:
            def og_get_size(media_type):
                return dict((p, int_or_none(self._og_search_property(
                    ':'.join((media_type, p)), webpage, default=None)))
                    for p in ('width', 'height'))

            size = og_get_size('video')
            if all(v is None for v in size.values()):
                size = og_get_size('image')

            formats = traverse_obj(
                re.finditer(r'<source\s+src="(?P<src>[^"]+)"\s+type="(?P<type>[^"]+)"', video_elements),
                (Ellipsis, {
                    'format_id': ('type', T(lambda s: s.partition('/')[2])),
                    'url': ('src', T(self._proto_relative_url)),
                    'ext': ('type', T(mimetype2ext)),
                }, T(lambda f: mung_format(f, size))))

            gif_json = self._search_regex(
                r'(?s)var\s+videoItem\s*=\s*(\{.*?\})',
                webpage, 'GIF code', fatal=False)
            MUST_BRANCH = (None, T(lambda _: None))
            formats.extend(traverse_obj(gif_json, (
                T(lambda j: self._parse_json(
                    j, video_id, transform_source=js_to_json, fatal=False)), {
                        'url': ('gifUrl', T(self._proto_relative_url)),
                        'filesize': ('size', T(int_or_none)),
                }, T(lambda f: mung_format(f, size, {
                    'format_id': 'gif',
                    'preference': -10,  # gifs are worse than videos
                    'ext': 'gif',
                    'acodec': 'none',
                    'vcodec': 'gif',
                    'container': 'gif',
                })), MUST_BRANCH)))
        else:
            formats = []

        # maybe add formats from JSON or page Twitter metadata
        if not any((u == media_url) for u in traverse_obj(formats, (Ellipsis, 'url'))):
            formats.append(mung_format(media_fmt))
        tw_url = traverse_obj(tw_formats, (0, 'url'))
        if not any((u == tw_url) for u in traverse_obj(formats, (Ellipsis, 'url'))):
            formats.extend(mung_format(f) for f in tw_formats)

        self._sort_formats(formats)

        return merge_dicts(traverse_obj(data, {
            'uploader_id': ('account_id', T(txt_or_none),
                            T(lambda a: a if int_or_none(a) != 0 else None)),
            'uploader': ('account', 'username', T(txt_or_none)),
            'uploader_url': ('account', 'avatar_url', T(url_or_none)),
            'like_count': ('upvote_count', T(int_or_none)),
            'dislike_count': ('downvote_count', T(int_or_none)),
            'comment_count': ('comment_count', T(int_or_none)),
            'age_limit': ('is_mature', T(lambda x: 18 if x else None)),
            'timestamp': (('updated_at', 'created_at'), T(parse_iso8601)),
            'release_timestamp': ('created_at', T(parse_iso8601)),
        }, get_all=False), traverse_obj(data, ('media', 0, 'metadata', {
            'title': ('title', T(txt_or_none)),
            'description': ('description', T(self.get_description)),
            'duration': ('duration', T(float_or_none)),
            'timestamp': (('updated_at', 'created_at'), T(parse_iso8601)),
            'release_timestamp': ('created_at', T(parse_iso8601)),
        })), {
            'id': video_id,
            'formats': formats,
            'title': self._og_search_title(webpage, default='Imgur video ' + video_id),
            'description': self.get_description(self._og_search_description(webpage)),
            'thumbnail': url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None)),
        })