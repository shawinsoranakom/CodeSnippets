def _extract_videos(self, root, video_id, embed_path='embed', record_path='record', record_subpath='embed'):
        embed_path = variadic(embed_path, (str, bytes, dict, set))
        record_path = variadic(record_path, (str, bytes, dict, set))
        record_subpath = variadic(record_subpath, (str, bytes, dict, set))

        entries = []
        if external_uri := traverse_obj(root, (
                ((*record_path, *record_subpath), embed_path), 'external', 'uri', {url_or_none}, any)):
            entries.append(self.url_result(external_uri))
        if playlist := traverse_obj(root, (*embed_path, 'playlist', {url_or_none})):
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                playlist, video_id, 'mp4', m3u8_id='hls', fatal=False)
        else:
            return entries

        video_cid = traverse_obj(
            root, (*embed_path, 'cid', {str}),
            (*record_path, *record_subpath, 'video', 'ref', '$link', {str}))
        did = traverse_obj(root, ('author', 'did', {str}))

        if did and video_cid:
            endpoint = self._get_service_endpoint(did, video_id)

            formats.append({
                'format_id': 'blob',
                'quality': 1,
                'url': update_url_query(
                    self._BLOB_URL_TMPL.format(endpoint), {'did': did, 'cid': video_cid}),
                **traverse_obj(root, (*embed_path, 'aspectRatio', {
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                })),
                **traverse_obj(root, (*record_path, *record_subpath, 'video', {
                    'filesize': ('size', {int_or_none}),
                    'ext': ('mimeType', {mimetype2ext}),
                })),
            })

            for sub_data in traverse_obj(root, (
                    *record_path, *record_subpath, 'captions', lambda _, v: v['file']['ref']['$link'])):
                subtitles.setdefault(sub_data.get('lang') or 'und', []).append({
                    'url': update_url_query(
                        self._BLOB_URL_TMPL.format(endpoint), {'did': did, 'cid': sub_data['file']['ref']['$link']}),
                    'ext': traverse_obj(sub_data, ('file', 'mimeType', {mimetype2ext})),
                })

        entries.append({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(root, {
                'id': ('uri', {url_basename}),
                'thumbnail': (*embed_path, 'thumbnail', {url_or_none}),
                'alt_title': (*embed_path, 'alt', {str}, filter),
                'uploader': ('author', 'displayName', {str}),
                'uploader_id': ('author', 'handle', {str}),
                'uploader_url': ('author', 'handle', {self._build_profile_url}),
                'channel_id': ('author', 'did', {str}),
                'channel_url': ('author', 'did', {self._build_profile_url}),
                'like_count': ('likeCount', {int_or_none}),
                'repost_count': ('repostCount', {int_or_none}),
                'comment_count': ('replyCount', {int_or_none}),
                'timestamp': ('indexedAt', {parse_iso8601}),
                'tags': ('labels', ..., 'val', {str}, all, {orderedSet}),
                'age_limit': (
                    'labels', ..., 'val', {lambda x: 18 if x in ('sexual', 'porn', 'graphic-media') else None}, any),
                'description': (*record_path, 'text', {str}, filter),
                'title': (*record_path, 'text', {lambda x: x.replace('\n', ' ')}, {truncate_string(left=72)}),
            }),
        })
        return entries