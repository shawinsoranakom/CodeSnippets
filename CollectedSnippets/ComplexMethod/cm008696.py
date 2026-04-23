def _extract_metadata_from_tabs(self, item_id, data):
        info = {'id': item_id}

        metadata_renderer = traverse_obj(data, ('metadata', 'channelMetadataRenderer'), expected_type=dict)
        if metadata_renderer:
            channel_id = traverse_obj(metadata_renderer, ('externalId', {self.ucid_or_none}),
                                      ('channelUrl', {self.ucid_from_url}))
            info.update({
                'channel': metadata_renderer.get('title'),
                'channel_id': channel_id,
            })
            if info['channel_id']:
                info['id'] = info['channel_id']
        else:
            metadata_renderer = traverse_obj(data, ('metadata', 'playlistMetadataRenderer'), expected_type=dict)

        # pageHeaderViewModel slow rollout began April 2024
        page_header_view_model = traverse_obj(data, (
            'header', 'pageHeaderRenderer', 'content', 'pageHeaderViewModel', {dict}))

        # We can get the uncropped banner/avatar by replacing the crop params with '=s0'
        # See: https://github.com/yt-dlp/yt-dlp/issues/2237#issuecomment-1013694714
        def _get_uncropped(url):
            return url_or_none((url or '').split('=')[0] + '=s0')

        avatar_thumbnails = self._extract_thumbnails(metadata_renderer, 'avatar')
        if avatar_thumbnails:
            uncropped_avatar = _get_uncropped(avatar_thumbnails[0]['url'])
            if uncropped_avatar:
                avatar_thumbnails.append({
                    'url': uncropped_avatar,
                    'id': 'avatar_uncropped',
                    'preference': 1,
                })

        channel_banners = (
            self._extract_thumbnails(data, ('header', ..., ('banner', 'mobileBanner', 'tvBanner')))
            or self._extract_thumbnails(
                page_header_view_model, ('banner', 'imageBannerViewModel', 'image'), final_key='sources'))
        for banner in channel_banners:
            banner['preference'] = -10

        if channel_banners:
            uncropped_banner = _get_uncropped(channel_banners[0]['url'])
            if uncropped_banner:
                channel_banners.append({
                    'url': uncropped_banner,
                    'id': 'banner_uncropped',
                    'preference': -5,
                })

        # Deprecated - remove primary_sidebar_renderer when layout discontinued
        primary_sidebar_renderer = self._extract_sidebar_info_renderer(data, 'playlistSidebarPrimaryInfoRenderer')
        playlist_header_renderer = traverse_obj(data, ('header', 'playlistHeaderRenderer'), expected_type=dict)

        primary_thumbnails = self._extract_thumbnails(
            primary_sidebar_renderer, ('thumbnailRenderer', ('playlistVideoThumbnailRenderer', 'playlistCustomThumbnailRenderer'), 'thumbnail'))
        playlist_thumbnails = self._extract_thumbnails(
            playlist_header_renderer, ('playlistHeaderBanner', 'heroPlaylistThumbnailRenderer', 'thumbnail'))

        info.update({
            'title': (traverse_obj(metadata_renderer, 'title')
                      or self._get_text(data, ('header', 'hashtagHeaderRenderer', 'hashtag'))
                      or info['id']),
            'availability': self._extract_availability(data),
            'channel_follower_count': (
                self._get_count(data, ('header', ..., 'subscriberCountText'))
                or traverse_obj(page_header_view_model, (
                    'metadata', 'contentMetadataViewModel', 'metadataRows', ..., 'metadataParts',
                    lambda _, v: 'subscribers' in v['text']['content'], 'text', 'content', {parse_count}, any))),
            'description': try_get(metadata_renderer, lambda x: x.get('description', '')),
            'tags': (traverse_obj(data, ('microformat', 'microformatDataRenderer', 'tags', ..., {str}))
                     or traverse_obj(metadata_renderer, ('keywords', {lambda x: x and shlex.split(x)}, ...))),
            'thumbnails': (primary_thumbnails or playlist_thumbnails) + avatar_thumbnails + channel_banners,
        })

        channel_handle = (
            traverse_obj(metadata_renderer, (('vanityChannelUrl', ('ownerUrls', ...)), {self.handle_from_url}), get_all=False)
            or traverse_obj(data, ('header', ..., 'channelHandleText', {self.handle_or_none}), get_all=False))

        if channel_handle:
            info.update({
                'uploader_id': channel_handle,
                'uploader_url': format_field(channel_handle, None, 'https://www.youtube.com/%s', default=None),
            })

        channel_badges = self._extract_badges(traverse_obj(data, ('header', ..., 'badges'), get_all=False))
        if self._has_badge(channel_badges, BadgeType.VERIFIED):
            info['channel_is_verified'] = True
        # Playlist stats is a text runs array containing [video count, view count, last updated].
        # last updated or (view count and last updated) may be missing.
        playlist_stats = get_first(
            (primary_sidebar_renderer, playlist_header_renderer), (('stats', 'briefStats', 'numVideosText'), ))

        last_updated_unix = self._parse_time_text(
            self._get_text(playlist_stats, 2)  # deprecated, remove when old layout discontinued
            or self._get_text(playlist_header_renderer, ('byline', 1, 'playlistBylineRenderer', 'text')))
        info['modified_date'] = strftime_or_none(last_updated_unix)

        info['view_count'] = self._get_count(playlist_stats, 1)
        if info['view_count'] is None:  # 0 is allowed
            info['view_count'] = self._get_count(playlist_header_renderer, 'viewCountText')
        if info['view_count'] is None:
            info['view_count'] = self._get_count(data, (
                'contents', 'twoColumnBrowseResultsRenderer', 'tabs', ..., 'tabRenderer', 'content', 'sectionListRenderer',
                'contents', ..., 'itemSectionRenderer', 'contents', ..., 'channelAboutFullMetadataRenderer', 'viewCountText'))

        info['playlist_count'] = self._get_count(playlist_stats, 0)
        if info['playlist_count'] is None:  # 0 is allowed
            info['playlist_count'] = self._get_count(playlist_header_renderer, ('byline', 0, 'playlistBylineRenderer', 'text'))

        if not info.get('channel_id'):
            owner = traverse_obj(playlist_header_renderer, 'ownerText')
            if not owner:  # Deprecated
                owner = traverse_obj(
                    self._extract_sidebar_info_renderer(data, 'playlistSidebarSecondaryInfoRenderer'),
                    ('videoOwner', 'videoOwnerRenderer', 'title'))
            owner_text = self._get_text(owner)
            browse_ep = traverse_obj(owner, ('runs', 0, 'navigationEndpoint', 'browseEndpoint')) or {}
            info.update({
                'channel': self._search_regex(r'^by (.+) and \d+ others?$', owner_text, 'uploader', default=owner_text),
                'channel_id': self.ucid_or_none(browse_ep.get('browseId')),
                'uploader_id': self.handle_from_url(urljoin('https://www.youtube.com', browse_ep.get('canonicalBaseUrl'))),
            })

        info.update({
            'uploader': info['channel'],
            'channel_url': format_field(info.get('channel_id'), None, 'https://www.youtube.com/channel/%s', default=None),
            'uploader_url': format_field(info.get('uploader_id'), None, 'https://www.youtube.com/%s', default=None),
        })

        return info