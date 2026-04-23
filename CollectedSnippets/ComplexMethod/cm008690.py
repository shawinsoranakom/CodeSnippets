def _extract_video(self, renderer):
        video_id = renderer.get('videoId')

        reel_header_renderer = traverse_obj(renderer, (
            'navigationEndpoint', 'reelWatchEndpoint', 'overlay', 'reelPlayerOverlayRenderer',
            'reelPlayerHeaderSupportedRenderers', 'reelPlayerHeaderRenderer'))

        title = self._get_text(renderer, 'title', 'headline') or self._get_text(reel_header_renderer, 'reelTitleText')
        description = self._get_text(renderer, 'descriptionSnippet', ('detailedMetadataSnippets', ..., 'snippetText'))

        duration = int_or_none(renderer.get('lengthSeconds'))
        if duration is None:
            duration = parse_duration(self._get_text(
                renderer, 'lengthText', ('thumbnailOverlays', ..., 'thumbnailOverlayTimeStatusRenderer', 'text')))
        if duration is None:
            # XXX: should write a parser to be more general to support more cases (e.g. shorts in shorts tab)
            duration = parse_duration(self._search_regex(
                r'(?i)(ago)(?!.*\1)\s+(?P<duration>[a-z0-9 ,]+?)(?:\s+[\d,]+\s+views)?(?:\s+-\s+play\s+short)?$',
                traverse_obj(renderer, ('title', 'accessibility', 'accessibilityData', 'label'), default='', expected_type=str),
                video_id, default=None, group='duration'))

        channel_id = traverse_obj(
            renderer, ('shortBylineText', 'runs', ..., 'navigationEndpoint', 'browseEndpoint', 'browseId'),
            expected_type=str, get_all=False)
        if not channel_id:
            channel_id = traverse_obj(reel_header_renderer, ('channelNavigationEndpoint', 'browseEndpoint', 'browseId'))

        channel_id = self.ucid_or_none(channel_id)

        overlay_style = traverse_obj(
            renderer, ('thumbnailOverlays', ..., 'thumbnailOverlayTimeStatusRenderer', 'style'),
            get_all=False, expected_type=str)
        badges = self._extract_badges(traverse_obj(renderer, 'badges'))
        owner_badges = self._extract_badges(traverse_obj(renderer, 'ownerBadges'))
        navigation_url = urljoin('https://www.youtube.com/', traverse_obj(
            renderer, ('navigationEndpoint', 'commandMetadata', 'webCommandMetadata', 'url'),
            expected_type=str)) or ''
        url = f'https://www.youtube.com/watch?v={video_id}'
        if overlay_style == 'SHORTS' or '/shorts/' in navigation_url:
            url = f'https://www.youtube.com/shorts/{video_id}'

        time_text = (self._get_text(renderer, 'publishedTimeText', 'videoInfo')
                     or self._get_text(reel_header_renderer, 'timestampText') or '')
        scheduled_timestamp = str_to_int(traverse_obj(renderer, ('upcomingEventData', 'startTime'), get_all=False))

        live_status = (
            'is_upcoming' if scheduled_timestamp is not None
            else 'was_live' if 'streamed' in time_text.lower()
            else 'is_live' if overlay_style == 'LIVE' or self._has_badge(badges, BadgeType.LIVE_NOW)
            else None)

        # videoInfo is a string like '50K views • 10 years ago'.
        view_count_text = self._get_text(renderer, 'viewCountText', 'shortViewCountText', 'videoInfo') or ''
        view_count = (0 if 'no views' in view_count_text.lower()
                      else self._get_count({'simpleText': view_count_text}))
        view_count_field = 'concurrent_view_count' if live_status in ('is_live', 'is_upcoming') else 'view_count'

        channel = (self._get_text(renderer, 'ownerText', 'shortBylineText')
                   or self._get_text(reel_header_renderer, 'channelTitleText'))

        channel_handle = traverse_obj(renderer, (
            'shortBylineText', 'runs', ..., 'navigationEndpoint',
            (('commandMetadata', 'webCommandMetadata', 'url'), ('browseEndpoint', 'canonicalBaseUrl'))),
            expected_type=self.handle_from_url, get_all=False)
        return {
            '_type': 'url',
            'ie_key': YoutubeIE.ie_key(),
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'duration': duration,
            'channel_id': channel_id,
            'channel': channel,
            'channel_url': f'https://www.youtube.com/channel/{channel_id}' if channel_id else None,
            'uploader': channel,
            'uploader_id': channel_handle,
            'uploader_url': format_field(channel_handle, None, 'https://www.youtube.com/%s', default=None),
            'thumbnails': self._extract_thumbnails(renderer, 'thumbnail'),
            'timestamp': (self._parse_time_text(time_text)
                          if self._configuration_arg('approximate_date', ie_key=YoutubeTabIE)
                          else None),
            'release_timestamp': scheduled_timestamp,
            'availability':
                'public' if self._has_badge(badges, BadgeType.AVAILABILITY_PUBLIC)
                else self._availability(
                    is_private=self._has_badge(badges, BadgeType.AVAILABILITY_PRIVATE) or None,
                    needs_premium=self._has_badge(badges, BadgeType.AVAILABILITY_PREMIUM) or None,
                    needs_subscription=self._has_badge(badges, BadgeType.AVAILABILITY_SUBSCRIPTION) or None,
                    is_unlisted=self._has_badge(badges, BadgeType.AVAILABILITY_UNLISTED) or None),
            view_count_field: view_count,
            'live_status': live_status,
            'channel_is_verified': True if self._has_badge(owner_badges, BadgeType.VERIFIED) else None,
        }