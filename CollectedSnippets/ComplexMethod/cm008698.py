def _extract_availability(self, data):
        """
        Gets the availability of a given playlist/tab.
        Note: Unless YouTube tells us explicitly, we do not assume it is public
        @param data: response
        """
        sidebar_renderer = self._extract_sidebar_info_renderer(data, 'playlistSidebarPrimaryInfoRenderer') or {}
        playlist_header_renderer = traverse_obj(data, ('header', 'playlistHeaderRenderer')) or {}
        player_header_privacy = playlist_header_renderer.get('privacy')

        badges = self._extract_badges(traverse_obj(sidebar_renderer, 'badges'))

        # Personal playlists, when authenticated, have a dropdown visibility selector instead of a badge
        privacy_setting_icon = get_first(
            (playlist_header_renderer, sidebar_renderer),
            ('privacyForm', 'dropdownFormFieldRenderer', 'dropdown', 'dropdownRenderer', 'entries',
             lambda _, v: v['privacyDropdownItemRenderer']['isSelected'], 'privacyDropdownItemRenderer', 'icon', 'iconType'),
            expected_type=str)

        microformats_is_unlisted = traverse_obj(
            data, ('microformat', 'microformatDataRenderer', 'unlisted'), expected_type=bool)

        return (
            'public' if (
                self._has_badge(badges, BadgeType.AVAILABILITY_PUBLIC)
                or player_header_privacy == 'PUBLIC'
                or privacy_setting_icon == 'PRIVACY_PUBLIC')
            else self._availability(
                is_private=(
                    self._has_badge(badges, BadgeType.AVAILABILITY_PRIVATE)
                    or player_header_privacy == 'PRIVATE' if player_header_privacy is not None
                    else privacy_setting_icon == 'PRIVACY_PRIVATE' if privacy_setting_icon is not None else None),
                is_unlisted=(
                    self._has_badge(badges, BadgeType.AVAILABILITY_UNLISTED)
                    or player_header_privacy == 'UNLISTED' if player_header_privacy is not None
                    else privacy_setting_icon == 'PRIVACY_UNLISTED' if privacy_setting_icon is not None
                    else microformats_is_unlisted if microformats_is_unlisted is not None else None),
                needs_subscription=self._has_badge(badges, BadgeType.AVAILABILITY_SUBSCRIPTION) or None,
                needs_premium=self._has_badge(badges, BadgeType.AVAILABILITY_PREMIUM) or None,
                needs_auth=False))