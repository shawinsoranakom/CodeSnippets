def _extract_notification_renderer(self, notification):
        video_id = traverse_obj(
            notification, ('navigationEndpoint', 'watchEndpoint', 'videoId'), expected_type=str)
        url = f'https://www.youtube.com/watch?v={video_id}'
        channel_id = None
        if not video_id:
            browse_ep = traverse_obj(
                notification, ('navigationEndpoint', 'browseEndpoint'), expected_type=dict)
            channel_id = self.ucid_or_none(traverse_obj(browse_ep, 'browseId', expected_type=str))
            post_id = self._search_regex(
                r'/post/(.+)', traverse_obj(browse_ep, 'canonicalBaseUrl', expected_type=str),
                'post id', default=None)
            if not channel_id or not post_id:
                return
            # The direct /post url redirects to this in the browser
            url = f'https://www.youtube.com/channel/{channel_id}/community?lb={post_id}'

        channel = traverse_obj(
            notification, ('contextualMenu', 'menuRenderer', 'items', 1, 'menuServiceItemRenderer', 'text', 'runs', 1, 'text'),
            expected_type=str)
        notification_title = self._get_text(notification, 'shortMessage')
        if notification_title:
            notification_title = notification_title.replace('\xad', '')  # remove soft hyphens
        # TODO: handle recommended videos
        title = self._search_regex(
            rf'{re.escape(channel or "")}[^:]+: (.+)', notification_title,
            'video title', default=None)
        timestamp = (self._parse_time_text(self._get_text(notification, 'sentTimeText'))
                     if self._configuration_arg('approximate_date', ie_key=YoutubeTabIE)
                     else None)
        return {
            '_type': 'url',
            'url': url,
            'ie_key': (YoutubeIE if video_id else YoutubeTabIE).ie_key(),
            'video_id': video_id,
            'title': title,
            'channel_id': channel_id,
            'channel': channel,
            'uploader': channel,
            'thumbnails': self._extract_thumbnails(notification, 'videoThumbnail'),
            'timestamp': timestamp,
        }