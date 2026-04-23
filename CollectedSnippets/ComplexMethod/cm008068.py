def extract_metadata(webpage):
            post_data = [self._parse_json(j, video_id, fatal=False) for j in re.findall(
                r'data-sjs>({.*?ScheduledServerJS.*?})</script>', webpage)]
            post = traverse_obj(post_data, (
                ..., 'require', ..., ..., ..., '__bbox', 'require', ..., ..., ..., '__bbox', 'result', 'data'), expected_type=dict) or []
            media = traverse_obj(post, (..., 'attachments', ..., lambda k, v: (
                k == 'media' and str(v['id']) == video_id and v['__typename'] == 'Video')), expected_type=dict)
            title = get_first(media, ('title', 'text'))
            description = get_first(media, ('creation_story', 'comet_sections', 'message', 'story', 'message', 'text'))
            page_title = title or self._html_search_regex((
                r'<h2\s+[^>]*class="uiHeaderTitle"[^>]*>(?P<content>[^<]*)</h2>',
                r'(?s)<span class="fbPhotosPhotoCaption".*?id="fbPhotoPageCaption"><span class="hasCaption">(?P<content>.*?)</span>',
                self._meta_regex('og:title'), self._meta_regex('twitter:title'), r'<title>(?P<content>.+?)</title>',
            ), webpage, 'title', default=None, group='content')
            description = description or self._html_search_meta(
                ['description', 'og:description', 'twitter:description'],
                webpage, 'description', default=None)
            uploader_data = (
                get_first(media, ('owner', {dict}))
                or get_first(post, ('video', 'creation_story', 'attachments', ..., 'media', lambda k, v: k == 'owner' and v['name']))
                or get_first(post, (..., 'video', lambda k, v: k == 'owner' and v['name']))
                or get_first(post, ('node', 'actors', ..., {dict}))
                or get_first(post, ('event', 'event_creator', {dict}))
                or get_first(post, ('video', 'creation_story', 'short_form_video_context', 'video_owner', {dict})) or {})
            uploader = uploader_data.get('name') or (
                clean_html(get_element_by_id('fbPhotoPageAuthorName', webpage))
                or self._search_regex(
                    (r'ownerName\s*:\s*"([^"]+)"', *self._og_regexes('title')), webpage, 'uploader', fatal=False))
            timestamp = int_or_none(self._search_regex(
                r'<abbr[^>]+data-utime=["\'](\d+)', webpage,
                'timestamp', default=None))
            thumbnail = self._html_search_meta(
                ['og:image', 'twitter:image'], webpage, 'thumbnail', default=None)
            # some webpages contain unretrievable thumbnail urls
            # like https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=10155168902769113&get_thumbnail=1
            # in https://www.facebook.com/yaroslav.korpan/videos/1417995061575415/
            if thumbnail and not re.search(r'\.(?:jpg|png)', thumbnail):
                thumbnail = None
            info_dict = {
                'description': description,
                'uploader': uploader,
                'uploader_id': uploader_data.get('id'),
                'timestamp': timestamp,
                'thumbnail': thumbnail,
                'view_count': parse_count(self._search_regex(
                    (r'\bviewCount\s*:\s*["\']([\d,.]+)', r'video_view_count["\']\s*:\s*(\d+)'),
                    webpage, 'view count', default=None)),
                'concurrent_view_count': get_first(post, (
                    ('video', (..., ..., 'attachments', ..., 'media')), 'liveViewerCount', {int_or_none})),
                **traverse_obj(post, (lambda _, v: video_id in v['url'], 'feedback', {
                    'like_count': ('likers', 'count', {int}),
                    'comment_count': ('total_comment_count', {int}),
                    'repost_count': ('share_count_reduced', {parse_count}),
                }), get_all=False),
            }

            info_json_ld = self._search_json_ld(webpage, video_id, default={})
            info_json_ld['title'] = (re.sub(r'\s*\|\s*Facebook$', '', title or info_json_ld.get('title') or page_title or '')
                                     or (description or '').replace('\n', ' ') or f'Facebook video #{video_id}')
            return merge_dicts(info_json_ld, info_dict)