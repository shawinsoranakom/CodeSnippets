def _real_extract(self, url):
        blog_1, blog_2, video_id = self._match_valid_url(url).groups()
        blog = blog_2 or blog_1

        url = f'http://{blog}.tumblr.com/post/{video_id}'
        webpage, urlh = self._download_webpage_handle(
            url, video_id, headers={'User-Agent': 'WhatsApp/2.0'})  # whatsapp ua bypasses problems

        redirect_url = urlh.url

        api_only = bool(self._search_regex(
            r'(tumblr.com|^)/(safe-mode|login_required|blog/view)',
            redirect_url, 'redirect', default=None))

        if api_only and not self._ACCESS_TOKEN:
            raise ExtractorError('Cannot get data for dashboard-only post without access token')

        post_json = {}
        if self._ACCESS_TOKEN:
            post_json = traverse_obj(
                self._download_json(
                    f'https://www.tumblr.com/api/v2/blog/{blog}/posts/{video_id}/permalink',
                    video_id, headers={'Authorization': f'Bearer {self._ACCESS_TOKEN}'}, fatal=False),
                ('response', 'timeline', 'elements', 0, {dict})) or {}
        content_json = traverse_obj(post_json, ((('trail', 0), None), 'content', ..., {dict}))

        # the url we're extracting from might be an original post or it might be a reblog.
        # if it's a reblog, og:description will be the reblogger's comment, not the uploader's.
        # content_json is always the op, so if it exists but has no text, there's no description
        if content_json:
            description = '\n\n'.join(
                item.get('text') for item in content_json if item.get('type') == 'text') or None
        else:
            description = self._og_search_description(webpage, default=None)
        uploader_id = traverse_obj(post_json, 'reblogged_root_name', 'blog_name')

        info_dict = {
            'id': video_id,
            'title': post_json.get('summary') or (blog if api_only else self._html_search_regex(
                r'(?s)<title>(?P<title>.*?)(?: \| Tumblr)?</title>', webpage, 'title', default=blog)),
            'description': description,
            'uploader_id': uploader_id,
            'uploader_url': f'https://{uploader_id}.tumblr.com/' if uploader_id else None,
            **traverse_obj(post_json, {
                # Try oldest post in reblog chain, fall back to timestamp of the post itself
                'timestamp': ((('trail', 0, 'post'), None), 'timestamp', {int_or_none}, any),
                'like_count': ('like_count', {int_or_none}),
                'repost_count': ('reblog_count', {int_or_none}),
                'tags': ('tags', ..., {str}),
            }),
            'age_limit': {True: 18, False: 0}.get(post_json.get('is_nsfw')),
        }

        # for tumblr's own video hosting
        fallback_format = None
        formats = []
        video_url = self._og_search_video_url(webpage, default=None)
        # for external video hosts
        entries = []
        ignored_providers = set()
        unknown_providers = set()

        for video_json in traverse_obj(content_json, lambda _, v: v['type'] in ('video', 'audio')):
            media_json = video_json.get('media') or {}
            if api_only and not media_json.get('url') and not video_json.get('url'):
                raise ExtractorError('Failed to find video data for dashboard-only post')
            provider = video_json.get('provider')

            if provider in ('tumblr', None):
                fallback_format = {
                    'url': media_json.get('url') or video_url,
                    'width': int_or_none(
                        media_json.get('width') or self._og_search_property('video:width', webpage, default=None)),
                    'height': int_or_none(
                        media_json.get('height') or self._og_search_property('video:height', webpage, default=None)),
                }
                continue
            elif provider in self._unsupported_providers:
                ignored_providers.add(provider)
                continue
            elif provider and provider not in self._providers:
                unknown_providers.add(provider)
            if video_json.get('url'):
                # external video host
                entries.append(self.url_result(
                    video_json['url'], self._providers.get(provider)))

        duration = None

        # iframes can supply duration and sometimes additional formats, so check for one
        iframe_url = self._search_regex(
            fr'src=\'(https?://www\.tumblr\.com/video/{blog}/{video_id}/[^\']+)\'',
            webpage, 'iframe url', default=None)
        if iframe_url:
            iframe = self._download_webpage(
                iframe_url, video_id, 'Downloading iframe page',
                headers={'Referer': redirect_url})

            options = self._parse_json(
                self._search_regex(
                    r'data-crt-options=(["\'])(?P<options>.+?)\1', iframe,
                    'hd video url', default='', group='options'),
                video_id, fatal=False)
            if options:
                duration = int_or_none(options.get('duration'))

                hd_url = options.get('hdUrl')
                if hd_url:
                    # there are multiple formats; extract them
                    # ignore other sources of width/height data as they may be wrong
                    sources = []
                    sd_url = self._search_regex(
                        r'<source[^>]+src=(["\'])(?P<url>.+?)\1', iframe,
                        'sd video url', default=None, group='url')
                    if sd_url:
                        sources.append((sd_url, 'sd'))
                    sources.append((hd_url, 'hd'))

                    formats = [{
                        'url': video_url,
                        'format_id': format_id,
                        'height': int_or_none(self._search_regex(
                            r'_(\d+)\.\w+$', video_url, 'height', default=None)),
                        'quality': quality,
                    } for quality, (video_url, format_id) in enumerate(sources)]

        if not formats and fallback_format:
            formats.append(fallback_format)

        if formats:
            # tumblr's own video is always above embeds
            entries.insert(0, {
                **info_dict,
                'formats': formats,
                'duration': duration,
                'thumbnail': (traverse_obj(video_json, ('poster', 0, 'url', {url_or_none}))
                              or self._og_search_thumbnail(webpage, default=None)),
            })

        if ignored_providers:
            if not entries:
                raise ExtractorError(f'None of embed providers are supported: {", ".join(ignored_providers)!s}', video_id=video_id, expected=True)
            else:
                self.report_warning(f'Skipped embeds from unsupported providers: {", ".join(ignored_providers)!s}', video_id)
        if unknown_providers:
            self.report_warning(f'Unrecognized providers, please report: {", ".join(unknown_providers)!s}', video_id)

        if not entries:
            self.raise_no_formats('No video could be found in this post', expected=True, video_id=video_id)
        if len(entries) == 1:
            return {
                **info_dict,
                **entries[0],
            }
        return {
            **info_dict,
            '_type': 'playlist',
            'entries': entries,
        }