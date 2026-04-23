def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_api('media', video_id)
        if not traverse_obj(data, ('media', 0, (
                ('type', {lambda t: t == 'video' or None}),
                ('metadata', 'is_animated'))), get_all=False):
            raise ExtractorError(f'{video_id} is not a video or animated image', expected=True)
        webpage = self._download_webpage(
            f'https://i.imgur.com/{video_id}.gifv', video_id, fatal=False) or ''
        formats = []

        media_fmt = traverse_obj(data, ('media', 0, {
            'url': ('url', {url_or_none}),
            'ext': ('ext', {str}),
            'width': ('width', {int_or_none}),
            'height': ('height', {int_or_none}),
            'filesize': ('size', {int_or_none}),
            'acodec': ('metadata', 'has_sound', {lambda b: None if b else 'none'}),
        }))
        media_url = media_fmt.get('url')
        if media_url:
            if not media_fmt.get('ext'):
                media_fmt['ext'] = mimetype2ext(traverse_obj(
                    data, ('media', 0, 'mime_type'))) or determine_ext(media_url)
            if traverse_obj(data, ('media', 0, 'type')) == 'image':
                media_fmt['acodec'] = 'none'
                media_fmt.setdefault('preference', -10)
            formats.append(media_fmt)

        video_elements = self._search_regex(
            r'(?s)<div class="video-elements">(.*?)</div>',
            webpage, 'video elements', default=None)

        if video_elements:
            def og_get_size(media_type):
                return {
                    p: int_or_none(self._og_search_property(f'{media_type}:{p}', webpage, default=None))
                    for p in ('width', 'height')
                }

            size = og_get_size('video')
            if not any(size.values()):
                size = og_get_size('image')

            formats = traverse_obj(
                re.finditer(r'<source\s+src="(?P<src>[^"]+)"\s+type="(?P<type>[^"]+)"', video_elements),
                (..., {
                    'format_id': ('type', {lambda s: s.partition('/')[2]}),
                    'url': ('src', {self._proto_relative_url}),
                    'ext': ('type', {mimetype2ext}),
                }))
            for f in formats:
                f.update(size)

            # We can get the original gif format from the webpage as well
            gif_json = traverse_obj(self._search_json(
                r'var\s+videoItem\s*=', webpage, 'GIF info', video_id,
                transform_source=js_to_json, fatal=False), {
                    'url': ('gifUrl', {self._proto_relative_url}),
                    'filesize': ('size', {int_or_none}),
            })
            if gif_json:
                gif_json.update(size)
                gif_json.update({
                    'format_id': 'gif',
                    'preference': -10,  # gifs < videos
                    'ext': 'gif',
                    'acodec': 'none',
                    'vcodec': 'gif',
                    'container': 'gif',
                })
                formats.append(gif_json)

        search = functools.partial(self._html_search_meta, html=webpage, default=None)

        twitter_fmt = {
            'format_id': 'twitter',
            'url': url_or_none(search('twitter:player:stream')),
            'ext': mimetype2ext(search('twitter:player:stream:content_type')),
            'width': int_or_none(search('twitter:width')),
            'height': int_or_none(search('twitter:height')),
        }
        if twitter_fmt['url']:
            formats.append(twitter_fmt)

        if not formats:
            self.raise_no_formats(
                f'No sources found for video {video_id}. Maybe a plain image?', expected=True)
        self._remove_duplicate_formats(formats)

        return {
            'title': self._og_search_title(webpage, default=None),
            'description': self.get_description(self._og_search_description(webpage, default='')),
            **traverse_obj(data, {
                'uploader_id': ('account_id', {lambda a: str(a) if int_or_none(a) else None}),
                'uploader': ('account', 'username', {lambda x: strip_or_none(x) or None}),
                'uploader_url': ('account', 'avatar_url', {url_or_none}),
                'like_count': ('upvote_count', {int_or_none}),
                'dislike_count': ('downvote_count', {int_or_none}),
                'comment_count': ('comment_count', {int_or_none}),
                'age_limit': ('is_mature', {lambda x: 18 if x else None}),
                'timestamp': (('updated_at', 'created_at'), {parse_iso8601}),
                'release_timestamp': ('created_at', {parse_iso8601}),
            }, get_all=False),
            **traverse_obj(data, ('media', 0, 'metadata', {
                'title': ('title', {lambda x: strip_or_none(x) or None}),
                'description': ('description', {self.get_description}),
                'duration': ('duration', {float_or_none}),
                'timestamp': (('updated_at', 'created_at'), {parse_iso8601}),
                'release_timestamp': ('created_at', {parse_iso8601}),
            }), get_all=False),
            'id': video_id,
            'formats': formats,
            'thumbnails': [{
                'url': thumbnail_url,
                'http_headers': {'Accept': '*/*'},
            }] if (thumbnail_url := search(['thumbnailUrl', 'twitter:image', 'og:image'])) else None,
            'http_headers': {'Accept': '*/*'},
        }