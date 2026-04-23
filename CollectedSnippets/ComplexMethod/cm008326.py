def _real_extract(self, url):
        slug = self._match_id(url)

        clip = self._download_gql(
            slug, [{
                'operationName': 'ShareClipRenderStatus',
                'variables': {'slug': slug},
            }],
            'Downloading clip GraphQL')[0]['data']['clip']

        if not clip:
            raise ExtractorError(
                'This clip is no longer available', expected=True)

        access_query = {
            'sig': clip['playbackAccessToken']['signature'],
            'token': clip['playbackAccessToken']['value'],
        }
        asset_default = traverse_obj(clip, ('assets', 0, {dict})) or {}
        asset_portrait = traverse_obj(clip, ('assets', 1, {dict})) or {}

        formats = []
        default_aspect_ratio = float_or_none(asset_default.get('aspectRatio'))
        formats.extend(traverse_obj(asset_default, ('videoQualities', lambda _, v: url_or_none(v['sourceURL']), {
            'url': ('sourceURL', {update_url_query(query=access_query)}),
            'format_id': ('quality', {str}),
            'height': ('quality', {int_or_none}),
            'fps': ('frameRate', {float_or_none}),
            'aspect_ratio': {value(default_aspect_ratio)},
        })))
        portrait_aspect_ratio = float_or_none(asset_portrait.get('aspectRatio'))
        for source in traverse_obj(asset_portrait, ('videoQualities', lambda _, v: url_or_none(v['sourceURL']))):
            formats.append({
                'url': update_url_query(source['sourceURL'], access_query),
                'format_id': join_nonempty('portrait', source.get('quality')),
                'height': int_or_none(source.get('quality')),
                'fps': float_or_none(source.get('frameRate')),
                'aspect_ratio': portrait_aspect_ratio,
                'quality': -2,
            })

        thumbnails = []
        thumb_asset_default_url = url_or_none(asset_default.get('thumbnailURL'))
        if thumb_asset_default_url:
            thumbnails.append({
                'id': 'default',
                'url': thumb_asset_default_url,
                'preference': 0,
            })
        if thumb_asset_portrait_url := url_or_none(asset_portrait.get('thumbnailURL')):
            thumbnails.append({
                'id': 'portrait',
                'url': thumb_asset_portrait_url,
                'preference': -1,
            })
        thumb_default_url = url_or_none(clip.get('thumbnailURL'))
        if thumb_default_url and thumb_default_url != thumb_asset_default_url:
            thumbnails.append({
                'id': 'small',
                'url': thumb_default_url,
                'preference': -2,
            })

        old_id = self._search_regex(r'%7C(\d+)(?:-\d+)?.mp4', formats[-1]['url'], 'old id', default=None)

        return {
            'id': clip.get('id') or slug,
            '_old_archive_ids': [make_archive_id(self, old_id)] if old_id else None,
            'display_id': slug,
            'formats': formats,
            'thumbnails': thumbnails,
            **traverse_obj(clip, {
                'title': ('title', {str}),
                'duration': ('durationSeconds', {int_or_none}),
                'view_count': ('viewCount', {int_or_none}),
                'timestamp': ('createdAt', {parse_iso8601}),
                'creators': ('broadcaster', 'displayName', {str}, filter, all),
                'channel': ('broadcaster', 'displayName', {str}),
                'channel_id': ('broadcaster', 'id', {str}),
                'channel_follower_count': ('broadcaster', 'followers', 'totalCount', {int_or_none}),
                'channel_is_verified': ('broadcaster', 'isPartner', {bool}),
                'uploader': ('curator', 'displayName', {str}),
                'uploader_id': ('curator', 'id', {str}),
                'categories': ('game', 'displayName', {str}, filter, all, filter),
            }),
        }