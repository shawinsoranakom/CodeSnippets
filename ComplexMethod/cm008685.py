def _real_extract(self, url):
        video_id, url = self._match_valid_url(url).group('id', 'url')
        media, webpage = {}, ''

        if self._get_cookies(url).get('sessionid'):
            info = traverse_obj(self._download_json(
                f'{self._API_BASE_URL}/media/{_id_to_pk(video_id)}/info/', video_id,
                fatal=False, errnote='Video info extraction failed',
                note='Downloading video info', headers=self._api_headers), ('items', 0))
            if info:
                media.update(info)
                return self._extract_product(media)

        api_check = self._download_json(
            f'{self._API_BASE_URL}/web/get_ruling_for_content/?content_type=MEDIA&target_id={_id_to_pk(video_id)}',
            video_id, headers=self._api_headers, fatal=False, note='Setting up session', errnote=False) or {}
        csrf_token = self._get_cookies('https://www.instagram.com').get('csrftoken')

        if not csrf_token:
            self.report_warning('No csrf token set by Instagram API', video_id)
        else:
            csrf_token = csrf_token.value if api_check.get('status') == 'ok' else None
            if not csrf_token:
                self.report_warning('Instagram API is not granting access', video_id)

        variables = {
            'shortcode': video_id,
            'child_comment_count': 3,
            'fetch_comment_count': 40,
            'parent_comment_count': 24,
            'has_threaded_comments': True,
        }
        general_info = self._download_json(
            'https://www.instagram.com/graphql/query/', video_id, fatal=False, errnote=False,
            headers={
                **self._api_headers,
                'X-CSRFToken': csrf_token or '',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url,
            }, query={
                'doc_id': '8845758582119845',
                'variables': json.dumps(variables, separators=(',', ':')),
            })

        if not general_info:
            self.report_warning('General metadata extraction failed (some metadata might be missing).', video_id)
            webpage, urlh = self._download_webpage_handle(url, video_id)
            shared_data = self._search_json(
                r'window\._sharedData\s*=', webpage, 'shared data', video_id, fatal=False) or {}

            if shared_data and self._LOGIN_URL not in urlh.url:
                media.update(traverse_obj(
                    shared_data, ('entry_data', 'PostPage', 0, 'graphql', 'shortcode_media'),
                    ('entry_data', 'PostPage', 0, 'media'), expected_type=dict) or {})
            else:
                self.report_warning('Main webpage is locked behind the login page. Retrying with embed webpage (some metadata might be missing).')
                webpage = self._download_webpage(
                    f'{url}/embed/', video_id, note='Downloading embed webpage', fatal=False) or ''
                additional_data = self._search_json(
                    r'window\.__additionalDataLoaded\s*\(\s*[^,]+,', webpage, 'additional data', video_id, fatal=False)
                if not additional_data and not media:
                    self.raise_login_required('Requested content is not available, rate-limit reached or login required')

                product_item = traverse_obj(additional_data, ('items', 0), expected_type=dict)
                if product_item:
                    media.update(product_item)
                    return self._extract_product(media)

                media.update(traverse_obj(
                    additional_data, ('graphql', 'shortcode_media'), 'shortcode_media', expected_type=dict) or {})

        else:
            xdt_shortcode_media = traverse_obj(general_info, ('data', 'xdt_shortcode_media', {dict})) or {}
            if not xdt_shortcode_media:
                error = join_nonempty('title', 'description', delim=': ', from_dict=api_check)
                if 'Restricted Video' in error:
                    self.raise_login_required(error)
                elif error:
                    raise ExtractorError(error, expected=True)
                elif len(video_id) > 28:
                    # It's a private post (video_id == shortcode + 28 extra characters)
                    # Only raise after getting empty response; sometimes "long"-shortcode posts are public
                    self.raise_login_required(
                        'This content is only available for registered users who follow this account')
                raise ExtractorError(
                    'Instagram sent an empty media response. Check if this post is accessible in your '
                    f'browser without being logged-in. If it is not, then u{self._login_hint()[1:]}. '
                    'Otherwise, if the post is accessible in browser without being logged-in'
                    f'{bug_reports_message(before=",")}', expected=True)
            media.update(xdt_shortcode_media)

        username = traverse_obj(media, ('owner', 'username')) or self._search_regex(
            r'"owner"\s*:\s*{\s*"username"\s*:\s*"(.+?)"', webpage, 'username', fatal=False)

        description = (
            traverse_obj(media, ('edge_media_to_caption', 'edges', 0, 'node', 'text'), expected_type=str)
            or media.get('caption'))
        if not description:
            description = self._search_regex(
                r'"caption"\s*:\s*"(.+?)"', webpage, 'description', default=None)
            if description is not None:
                description = lowercase_escape(description)

        video_url = media.get('video_url')
        if not video_url:
            nodes = traverse_obj(media, ('edge_sidecar_to_children', 'edges', ..., 'node'), expected_type=dict) or []
            if nodes:
                return self.playlist_result(
                    self._extract_nodes(nodes, True), video_id,
                    format_field(username, None, 'Post by %s'), description)
            raise ExtractorError('There is no video in this post', expected=True)

        formats = [{
            'url': video_url,
            'width': self._get_dimension('width', media, webpage),
            'height': self._get_dimension('height', media, webpage),
        }]
        dash = traverse_obj(media, ('dash_info', 'video_dash_manifest'))
        if dash:
            formats.extend(self._parse_mpd_formats(self._parse_xml(dash, video_id), mpd_id='dash'))

        comment_data = traverse_obj(media, ('edge_media_to_parent_comment', 'edges'))
        comments = [{
            'author': traverse_obj(comment_dict, ('node', 'owner', 'username')),
            'author_id': traverse_obj(comment_dict, ('node', 'owner', 'id')),
            'id': traverse_obj(comment_dict, ('node', 'id')),
            'text': traverse_obj(comment_dict, ('node', 'text')),
            'timestamp': traverse_obj(comment_dict, ('node', 'created_at'), expected_type=int_or_none),
        } for comment_dict in comment_data] if comment_data else None

        display_resources = (
            media.get('display_resources')
            or [{'src': media.get(key)} for key in ('display_src', 'display_url')]
            or [{'src': self._og_search_thumbnail(webpage)}])
        thumbnails = [{
            'url': thumbnail['src'],
            'width': thumbnail.get('config_width'),
            'height': thumbnail.get('config_height'),
        } for thumbnail in display_resources if thumbnail.get('src')]

        return {
            'id': video_id,
            'formats': formats,
            'title': media.get('title') or f'Video by {username}',
            'description': description,
            'duration': float_or_none(media.get('video_duration')),
            'timestamp': traverse_obj(media, 'taken_at_timestamp', 'date', expected_type=int_or_none),
            'uploader_id': traverse_obj(media, ('owner', 'id')),
            'uploader': traverse_obj(media, ('owner', 'full_name')),
            'channel': username,
            'like_count': self._get_count(media, 'likes', 'preview_like') or str_to_int(self._search_regex(
                r'data-log-event="likeCountClick"[^>]*>[^\d]*([\d,\.]+)', webpage, 'like count', fatal=False)),
            'comment_count': self._get_count(media, 'comments', 'preview_comment', 'to_comment', 'to_parent_comment'),
            'comments': comments,
            'thumbnails': thumbnails,
            'http_headers': {
                'Referer': 'https://www.instagram.com/',
            },
        }