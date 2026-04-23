def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._call_api(
            f'posts/{video_id}', video_id, query={
                'fields[media]': 'download_url,mimetype,size_bytes,file_name',
                'fields[post]': 'comment_count,content,embed,image,like_count,post_file,published_at,title,current_user_can_view',
                'fields[user]': 'full_name,url',
                'fields[post_tag]': 'value',
                'fields[campaign]': 'url,name,patron_count',
                'json-api-use-default-includes': 'false',
                'include': 'audio,user,user_defined_tags,campaign,attachments_media',
            })
        attributes = post['data']['attributes']
        info = traverse_obj(attributes, {
            'title': ('title', {str.strip}),
            'description': ('content', {clean_html}),
            'thumbnail': ('image', ('large_url', 'url'), {url_or_none}, any),
            'timestamp': ('published_at', {parse_iso8601}),
            'like_count': ('like_count', {int_or_none}),
            'comment_count': ('comment_count', {int_or_none}),
        })

        seen_media_ids = set()
        entries = []
        idx = 0
        for include in traverse_obj(post, ('included', lambda _, v: v['type'])):
            include_type = include['type']
            if include_type == 'media':
                media_attributes = traverse_obj(include, ('attributes', {dict})) or {}
                download_url = url_or_none(media_attributes.get('download_url'))
                ext = mimetype2ext(media_attributes.get('mimetype'))

                # if size_bytes is None, this media file is likely unavailable
                # See: https://github.com/yt-dlp/yt-dlp/issues/4608
                size_bytes = int_or_none(media_attributes.get('size_bytes'))
                if download_url and ext in KNOWN_EXTENSIONS and size_bytes is not None:
                    idx += 1
                    entries.append({
                        'id': f'{video_id}-{idx}',
                        'ext': ext,
                        'filesize': size_bytes,
                        'url': download_url,
                        'alt_title': traverse_obj(media_attributes, ('file_name', {str})),
                    })
                if media_id := traverse_obj(include, ('id', {str})):
                    seen_media_ids.add(media_id)

            elif include_type == 'user':
                info.update(traverse_obj(include, {
                    'uploader': ('attributes', 'full_name', {str}),
                    'uploader_id': ('id', {str_or_none}),
                    'uploader_url': ('attributes', 'url', {url_or_none}),
                }))

            elif include_type == 'post_tag':
                if post_tag := traverse_obj(include, ('attributes', 'value', {str})):
                    info.setdefault('tags', []).append(post_tag)

            elif include_type == 'campaign':
                info.update(traverse_obj(include, {
                    'channel': ('attributes', 'title', {str}),
                    'channel_id': ('id', {str_or_none}),
                    'channel_url': ('attributes', 'url', {url_or_none}),
                    'channel_follower_count': ('attributes', 'patron_count', {int_or_none}),
                }))

        if embed_url := traverse_obj(attributes, ('embed', 'url', {url_or_none})):
            # Convert useless vimeo.com URLs to useful player.vimeo.com embed URLs
            vimeo_id, vimeo_hash = self._search_regex(
                r'//vimeo\.com/(\d+)(?:/([\da-f]+))?', embed_url,
                'vimeo id', group=(1, 2), default=(None, None))
            if vimeo_id:
                embed_url = update_url_query(
                    f'https://player.vimeo.com/video/{vimeo_id}',
                    {'h': vimeo_hash or []})
            if VimeoIE.suitable(embed_url):
                entry = self.url_result(
                    VimeoIE._smuggle_referrer(embed_url, self._HTTP_HEADERS['referer']),
                    VimeoIE, url_transparent=True)
            else:
                entry = self.url_result(smuggle_url(embed_url, self._HTTP_HEADERS))

            if urlh := self._request_webpage(
                embed_url, video_id, 'Checking embed URL', headers=self._HTTP_HEADERS,
                fatal=False, errnote=False, expected_status=(403, 429),  # Ignore Vimeo 429's
            ):
                # Password-protected vids.io embeds return 403 errors w/o --video-password or session cookie
                if VidsIoIE.suitable(embed_url) or urlh.status != 403:
                    entries.append(entry)

        post_file = traverse_obj(attributes, ('post_file', {dict}))
        if post_file:
            name = post_file.get('name')
            ext = determine_ext(name)
            if ext in KNOWN_EXTENSIONS:
                entries.append({
                    'id': video_id,
                    'ext': ext,
                    'url': post_file['url'],
                })
            elif name == 'video' or determine_ext(post_file.get('url')) == 'm3u8':
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    post_file['url'], video_id, headers=self._HTTP_HEADERS)
                for f in formats:
                    f['http_headers'] = self._HTTP_HEADERS
                entries.append({
                    'id': video_id,
                    'formats': formats,
                    'subtitles': subtitles,
                })
            if media_id := traverse_obj(post_file, ('media_id', {int}, {str_or_none})):
                seen_media_ids.add(media_id)

        for media_id in traverse_obj(attributes, (
            'content', {find_elements(attr='data-media-id', value=r'\d+', regex=True, html=True)},
            ..., {extract_attributes}, 'data-media-id',
        )):
            # Inlined media may be duplicates of what was extracted above
            if media_id in seen_media_ids:
                continue
            if media := self._extract_from_media_api(media_id):
                entries.append(media)
                seen_media_ids.add(media_id)

        can_view_post = traverse_obj(attributes, 'current_user_can_view')
        comments = None
        if can_view_post and info.get('comment_count'):
            comments = self.extract_comments(video_id)

        if not entries and can_view_post is False:
            self.raise_no_formats('You do not have access to this post', video_id=video_id, expected=True)
        elif not entries:
            self.raise_no_formats('No supported media found in this post', video_id=video_id, expected=True)
        elif len(entries) == 1:
            info.update(entries[0])
        else:
            for entry in entries:
                entry.update(info)
            return self.playlist_result(entries, video_id, **info, __post_extractor=comments)

        info['id'] = video_id
        info['__post_extractor'] = comments
        return info