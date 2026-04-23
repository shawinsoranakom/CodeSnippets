def _extract_metadata(self, video_id, webpage):
        search_meta = ((lambda x: self._html_search_meta(x, webpage, default=None)) if webpage else (lambda x: None))
        player_response = self._search_json(
            self._YT_INITIAL_PLAYER_RESPONSE_RE, webpage, 'initial player response',
            video_id, default={})
        initial_data = self._search_json(
            self._YT_INITIAL_DATA_RE, webpage, 'initial data', video_id, default={})

        ytcfg = {}
        for j in re.findall(r'yt\.setConfig\(\s*(?P<json>{\s*(?s:.+?)\s*})\s*\);', webpage):  # ~June 2010
            ytcfg.update(self._parse_json(j, video_id, fatal=False, ignore_extra=True, transform_source=js_to_json, errnote='') or {})

        # XXX: this also may contain a 'ptchn' key
        player_config = (
            self._search_json(
                r'(?:yt\.playerConfig|ytplayer\.config|swfConfig)\s*=',
                webpage, 'player config', video_id, default=None)
            or ytcfg.get('PLAYER_CONFIG') or {})

        # XXX: this may also contain a 'creator' key.
        swf_args = self._search_json(r'swfArgs\s*=', webpage, 'swf config', video_id, default={})
        if swf_args and not traverse_obj(player_config, ('args',)):
            player_config['args'] = swf_args

        if not player_response:
            # April 2020
            player_response = self._parse_json(
                traverse_obj(player_config, ('args', 'player_response')) or '{}', video_id, fatal=False)

        initial_data_video = traverse_obj(
            initial_data, ('contents', 'twoColumnWatchNextResults', 'results', 'results', 'contents', ..., 'videoPrimaryInfoRenderer'),
            expected_type=dict, get_all=False, default={})

        video_details = traverse_obj(
            player_response, 'videoDetails', expected_type=dict, get_all=False, default={})

        microformats = traverse_obj(
            player_response, ('microformat', 'playerMicroformatRenderer'), expected_type=dict, get_all=False, default={})

        video_title = (
            video_details.get('title')
            or YoutubeBaseInfoExtractor._get_text(microformats, 'title')
            or YoutubeBaseInfoExtractor._get_text(initial_data_video, 'title')
            or traverse_obj(player_config, ('args', 'title'))
            or self._extract_webpage_title(webpage)
            or search_meta(['og:title', 'twitter:title', 'title']))

        def id_from_url(url, type_):
            return self._search_regex(
                rf'(?:{type_})/([^/#&?]+)', url or '', f'{type_} id', default=None)

        # XXX: would the get_elements_by_... functions be better suited here?
        _CHANNEL_URL_HREF_RE = r'href="[^"]*(?P<url>https?://www\.youtube\.com/(?:user|channel)/[^"]+)"'
        uploader_or_channel_url = self._search_regex(
            [fr'<(?:link\s*itemprop=\"url\"|a\s*id=\"watch-username\").*?\b{_CHANNEL_URL_HREF_RE}>',  # @fd05024
             fr'<div\s*id=\"(?:watch-channel-stats|watch-headline-user-info)\"[^>]*>\s*<a[^>]*\b{_CHANNEL_URL_HREF_RE}'],  # ~ May 2009, ~June 2012
            webpage, 'uploader or channel url', default=None)

        owner_profile_url = url_or_none(microformats.get('ownerProfileUrl'))  # @a6211d2

        # Uploader refers to the /user/ id ONLY
        uploader_id = (
            id_from_url(owner_profile_url, 'user')
            or id_from_url(uploader_or_channel_url, 'user')
            or ytcfg.get('VIDEO_USERNAME'))
        uploader_url = f'https://www.youtube.com/user/{uploader_id}' if uploader_id else None

        # XXX: do we want to differentiate uploader and channel?
        uploader = (
            self._search_regex(
                [r'<a\s*id="watch-username"[^>]*>\s*<strong>([^<]+)</strong>',  # June 2010
                 r'var\s*watchUsername\s*=\s*\'(.+?)\';',  # ~May 2009
                 r'<div\s*\bid=\"watch-channel-stats"[^>]*>\s*<a[^>]*>\s*(.+?)\s*</a',  # ~May 2009
                 r'<a\s*id="watch-userbanner"[^>]*title="\s*(.+?)\s*"'],  # ~June 2012
                webpage, 'uploader', default=None)
            or self._html_search_regex(
                [r'(?s)<div\s*class="yt-user-info".*?<a[^>]*[^>]*>\s*(.*?)\s*</a',  # March 2016
                 r'(?s)<a[^>]*yt-user-name[^>]*>\s*(.*?)\s*</a'],  # july 2013
                get_element_by_id('watch7-user-header', webpage), 'uploader', default=None)
            or self._html_search_regex(
                r'<button\s*href="/user/[^>]*>\s*<span[^>]*>\s*(.+?)\s*<',  # April 2012
                get_element_by_id('watch-headline-user-info', webpage), 'uploader', default=None)
            or traverse_obj(player_config, ('args', 'creator'))
            or video_details.get('author'))

        channel_id = str_or_none(
            video_details.get('channelId')
            or microformats.get('externalChannelId')
            or search_meta('channelId')
            or self._search_regex(
                r'data-channel-external-id=(["\'])(?P<id>(?:(?!\1).)+)\1',  # @b45a9e6
                webpage, 'channel id', default=None, group='id')
            or id_from_url(owner_profile_url, 'channel')
            or id_from_url(uploader_or_channel_url, 'channel')
            or traverse_obj(player_config, ('args', 'ucid')))

        channel_url = f'https://www.youtube.com/channel/{channel_id}' if channel_id else None
        duration = int_or_none(
            video_details.get('lengthSeconds')
            or microformats.get('lengthSeconds')
            or traverse_obj(player_config, ('args', ('length_seconds', 'l')), get_all=False)
            or parse_duration(search_meta('duration')))
        description = (
            video_details.get('shortDescription')
            or YoutubeBaseInfoExtractor._get_text(microformats, 'description')
            or clean_html(get_element_by_id('eow-description', webpage))  # @9e6dd23
            or search_meta(['description', 'og:description', 'twitter:description']))

        upload_date = unified_strdate(
            dict_get(microformats, ('uploadDate', 'publishDate'))
            or search_meta(['uploadDate', 'datePublished'])
            or self._search_regex(
                [r'(?s)id="eow-date.*?>\s*(.*?)\s*</span>',
                 r'(?:id="watch-uploader-info".*?>.*?|["\']simpleText["\']\s*:\s*["\'])(?:Published|Uploaded|Streamed live|Started) on (.+?)[<"\']',  # @7998520
                 r'class\s*=\s*"(?:watch-video-date|watch-video-added post-date)"[^>]*>\s*([^<]+?)\s*<'],  # ~June 2010, ~Jan 2009 (respectively)
                webpage, 'upload date', default=None))

        return {
            'title': video_title,
            'description': description,
            'upload_date': upload_date,
            'uploader': uploader,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'duration': duration,
            'uploader_url': uploader_url,
            'uploader_id': uploader_id,
        }