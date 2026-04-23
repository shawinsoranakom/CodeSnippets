def _real_extract(self, url):
        user, post_id = self._match_valid_url(url).group('user', 'post_id')

        auth_headers = {}
        auth_cookie = self._get_cookies('https://boosty.to/').get('auth')
        if auth_cookie is not None:
            try:
                auth_data = json.loads(urllib.parse.unquote(auth_cookie.value))
                auth_headers['Authorization'] = f'Bearer {auth_data["accessToken"]}'
            except (json.JSONDecodeError, KeyError):
                self.report_warning(f'Failed to extract token from auth cookie{bug_reports_message()}')

        post = self._download_json(
            f'https://api.boosty.to/v1/blog/{user}/post/{post_id}', post_id,
            note='Downloading post data', errnote='Unable to download post data', headers=auth_headers)

        post_title = post.get('title')
        if not post_title:
            self.report_warning('Unable to extract post title. Falling back to parsing html page')
            webpage = self._download_webpage(url, video_id=post_id)
            post_title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)

        common_metadata = {
            'title': post_title,
            **traverse_obj(post, {
                'channel': ('user', 'name', {str}),
                'channel_id': ('user', 'id', {str_or_none}),
                'timestamp': ('createdAt', {int_or_none}),
                'release_timestamp': ('publishTime', {int_or_none}),
                'modified_timestamp': ('updatedAt', {int_or_none}),
                'tags': ('tags', ..., 'title', {str}),
                'like_count': ('count', 'likes', {int_or_none}),
            }),
        }
        entries = []
        for item in traverse_obj(post, ('data', ..., {dict})):
            item_type = item.get('type')
            if item_type == 'video' and url_or_none(item.get('url')):
                entries.append(self.url_result(item['url'], YoutubeIE))
            elif item_type == 'ok_video':
                video_id = item.get('id') or post_id
                entries.append({
                    'id': video_id,
                    'alt_title': post_title,
                    'formats': self._extract_formats(item.get('playerUrls'), video_id),
                    **common_metadata,
                    **traverse_obj(item, {
                        'title': ('title', {str}),
                        'duration': ('duration', {int_or_none}),
                        'view_count': ('viewsCounter', {int_or_none}),
                        'thumbnail': (('preview', 'defaultPreview'), {url_or_none}),
                    }, get_all=False)})

        if not entries and not post.get('hasAccess'):
            self.raise_login_required('This post requires a subscription', metadata_available=True)
        elif not entries:
            raise ExtractorError('No videos found', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, post_id, post_title, **common_metadata)