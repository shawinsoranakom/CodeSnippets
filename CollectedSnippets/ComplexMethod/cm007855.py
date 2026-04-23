def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = mobj.group('url')

        webpage = self._download_webpage(url, video_id)

        (media, video_url, description, thumbnail, timestamp, uploader,
         uploader_id, like_count, comment_count, comments, height,
         width) = [None] * 12

        shared_data = self._parse_json(
            self._search_regex(
                r'window\._sharedData\s*=\s*({.+?});',
                webpage, 'shared data', default='{}'),
            video_id, fatal=False)
        if shared_data:
            media = try_get(
                shared_data,
                (lambda x: x['entry_data']['PostPage'][0]['graphql']['shortcode_media'],
                 lambda x: x['entry_data']['PostPage'][0]['media']),
                dict)
        # _sharedData.entry_data.PostPage is empty when authenticated (see
        # https://github.com/ytdl-org/youtube-dl/pull/22880)
        if not media:
            additional_data = self._parse_json(
                self._search_regex(
                    r'window\.__additionalDataLoaded\s*\(\s*[^,]+,\s*({.+?})\s*\)\s*;',
                    webpage, 'additional data', default='{}'),
                video_id, fatal=False)
            if additional_data:
                media = try_get(
                    additional_data, lambda x: x['graphql']['shortcode_media'],
                    dict)
        if media:
            video_url = media.get('video_url')
            height = int_or_none(media.get('dimensions', {}).get('height'))
            width = int_or_none(media.get('dimensions', {}).get('width'))
            description = try_get(
                media, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                compat_str) or media.get('caption')
            title = media.get('title')
            thumbnail = media.get('display_src') or media.get('display_url')
            duration = float_or_none(media.get('video_duration'))
            timestamp = int_or_none(media.get('taken_at_timestamp') or media.get('date'))
            uploader = media.get('owner', {}).get('full_name')
            uploader_id = media.get('owner', {}).get('username')

            def get_count(keys, kind):
                if not isinstance(keys, (list, tuple)):
                    keys = [keys]
                for key in keys:
                    count = int_or_none(try_get(
                        media, (lambda x: x['edge_media_%s' % key]['count'],
                                lambda x: x['%ss' % kind]['count'])))
                    if count is not None:
                        return count
            like_count = get_count('preview_like', 'like')
            comment_count = get_count(
                ('preview_comment', 'to_comment', 'to_parent_comment'), 'comment')

            comments = [{
                'author': comment.get('user', {}).get('username'),
                'author_id': comment.get('user', {}).get('id'),
                'id': comment.get('id'),
                'text': comment.get('text'),
                'timestamp': int_or_none(comment.get('created_at')),
            } for comment in media.get(
                'comments', {}).get('nodes', []) if comment.get('text')]
            if not video_url:
                edges = try_get(
                    media, lambda x: x['edge_sidecar_to_children']['edges'],
                    list) or []
                if edges:
                    entries = []
                    for edge_num, edge in enumerate(edges, start=1):
                        node = try_get(edge, lambda x: x['node'], dict)
                        if not node:
                            continue
                        node_video_url = url_or_none(node.get('video_url'))
                        if not node_video_url:
                            continue
                        entries.append({
                            'id': node.get('shortcode') or node['id'],
                            'title': node.get('title') or 'Video %d' % edge_num,
                            'url': node_video_url,
                            'thumbnail': node.get('display_url'),
                            'duration': float_or_none(node.get('video_duration')),
                            'width': int_or_none(try_get(node, lambda x: x['dimensions']['width'])),
                            'height': int_or_none(try_get(node, lambda x: x['dimensions']['height'])),
                            'view_count': int_or_none(node.get('video_view_count')),
                        })
                    return self.playlist_result(
                        entries, video_id,
                        'Post by %s' % uploader_id if uploader_id else None,
                        description)

        if not video_url:
            video_url = self._og_search_video_url(webpage, secure=False)

        formats = [{
            'url': video_url,
            'width': width,
            'height': height,
        }]

        if not uploader_id:
            uploader_id = self._search_regex(
                r'"owner"\s*:\s*{\s*"username"\s*:\s*"(.+?)"',
                webpage, 'uploader id', fatal=False)

        if not description:
            description = self._search_regex(
                r'"caption"\s*:\s*"(.+?)"', webpage, 'description', default=None)
            if description is not None:
                description = lowercase_escape(description)

        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'formats': formats,
            'ext': 'mp4',
            'title': title or 'Video by %s' % uploader_id,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'uploader': uploader,
            'like_count': like_count,
            'comment_count': comment_count,
            'comments': comments,
        }