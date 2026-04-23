def _real_extract(self, url):
        url, data, headers = self._unsmuggle_headers(url)
        if 'Referer' not in headers:
            headers['Referer'] = url

        # Extract ID from URL
        mobj = self._match_valid_url(url).groupdict()
        video_id, unlisted_hash = mobj['id'], mobj.get('unlisted_hash')
        if unlisted_hash:
            return self._extract_from_api(video_id, unlisted_hash)

        if any(p in url for p in ('play_redirect_hls', 'moogaloop.swf')):
            url = 'https://vimeo.com/' + video_id

        album_id = self._search_regex(
            r'vimeo\.com/(?:album|showcase)/([0-9]+)/', url, 'album id', default=None)
        if album_id:
            # Detect password-protected showcase video => POST album password => set cookies
            self._get_album_data_and_hashed_pass(album_id, False, None)

        parsed_url = urllib.parse.urlparse(url)
        is_secure = parsed_url.scheme == 'https'
        try:
            # Retrieve video webpage to extract further information
            webpage, urlh = self._download_webpage_handle(
                url, video_id, headers=headers, impersonate=is_secure)
            redirect_url = urlh.url
        except ExtractorError as error:
            if not isinstance(error.cause, HTTPError) or error.cause.status not in (403, 429):
                raise
            errmsg = error.cause.response.read()
            if b'Because of its privacy settings, this video cannot be played here' in errmsg:
                raise ExtractorError(self._REFERER_HINT, expected=True)
            # 403 == vimeo.com TLS fingerprint or DC IP block; 429 == player.vimeo.com TLS FP block
            status = error.cause.status
            dcip_msg = 'If you are using a data center IP or VPN/proxy, your IP may be blocked'
            if target := error.cause.response.extensions.get('impersonate'):
                raise ExtractorError(
                    f'Got HTTP Error {status} when using impersonate target "{target}". {dcip_msg}')
            elif not is_secure:
                raise ExtractorError(f'Got HTTP Error {status}. {dcip_msg}', expected=True)
            raise ExtractorError(
                'This request has been blocked due to its TLS fingerprint. Install a '
                'required impersonation dependency if possible, or else if you are okay with '
                f'{self._downloader._format_err("compromising your security/cookies", "light red")}, '
                f'try replacing "https:" with "http:" in the input URL. {dcip_msg}.', expected=True)

        if parsed_url.hostname == 'player.vimeo.com':
            config = self._search_json(
                r'\b(?:playerC|c)onfig\s*=', webpage, 'info section', video_id)
            if config.get('view') == 4:
                config = self._verify_player_video_password(
                    redirect_url, video_id, headers)
            info = self._parse_config(config, video_id)
            source_format = self._extract_original_format(
                f'https://vimeo.com/{video_id}', video_id, unlisted_hash)
            if source_format:
                info['formats'].append(source_format)
            return info

        vimeo_config = self._extract_vimeo_config(webpage, video_id, default=None)
        if vimeo_config:
            seed_status = vimeo_config.get('seed_status') or {}
            if seed_status.get('state') == 'failed':
                raise ExtractorError(
                    '{} said: {}'.format(self.IE_NAME, seed_status['title']),
                    expected=True)

        cc_license = None
        timestamp = None
        video_description = None
        info_dict = {}
        config_url = None

        channel_id = self._search_regex(
            r'vimeo\.com/channels/([^/?#]+)', url, 'channel id', default=None)
        if channel_id:
            config_url = self._extract_config_url(webpage, default=None)
            video_description = clean_html(get_element_by_class('description', webpage))
            info_dict.update({
                'channel_id': channel_id,
                'channel_url': 'https://vimeo.com/channels/' + channel_id,
            })
        if not config_url:
            page_config = self._parse_json(self._search_regex(
                r'vimeo\.(?:clip|vod_title)_page_config\s*=\s*({.+?});',
                webpage, 'page config', default='{}'), video_id, fatal=False)
            if not page_config:
                return self._extract_from_api(video_id)
            config_url = page_config['player']['config_url']
            cc_license = page_config.get('cc_license')
            clip = page_config.get('clip') or {}
            timestamp = clip.get('uploaded_on')
            video_description = clean_html(
                clip.get('description') or page_config.get('description_html_escaped'))
        config = self._download_json(config_url, video_id)
        video = config.get('video') or {}
        vod = video.get('vod') or {}

        def is_rented():
            if '>You rented this title.<' in webpage:
                return True
            if try_get(config, lambda x: x['user']['purchased']):
                return True
            for purchase_option in (vod.get('purchase_options') or []):
                if purchase_option.get('purchased'):
                    return True
                label = purchase_option.get('label_string')
                if label and (label.startswith('You rented this') or label.endswith(' remaining')):
                    return True
            return False

        if is_rented() and vod.get('is_trailer'):
            feature_id = vod.get('feature_id')
            if feature_id and not data.get('force_feature_id', False):
                return self.url_result(smuggle_url(
                    f'https://player.vimeo.com/player/{feature_id}',
                    {'force_feature_id': True}), 'Vimeo')

        if not video_description:
            video_description = self._html_search_regex(
                r'(?s)<div\s+class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
                webpage, 'description', default=None)
        if not video_description:
            video_description = self._html_search_meta(
                ['description', 'og:description', 'twitter:description'],
                webpage, default=None)
        if not video_description:
            self.report_warning('Cannot find video description')

        if not timestamp:
            timestamp = self._search_regex(
                r'<time[^>]+datetime="([^"]+)"', webpage,
                'timestamp', default=None)

        view_count = int_or_none(self._search_regex(r'UserPlays:(\d+)', webpage, 'view count', default=None))
        like_count = int_or_none(self._search_regex(r'UserLikes:(\d+)', webpage, 'like count', default=None))
        comment_count = int_or_none(self._search_regex(r'UserComments:(\d+)', webpage, 'comment count', default=None))

        formats = []

        source_format = self._extract_original_format(
            'https://vimeo.com/' + video_id, video_id, video.get('unlisted_hash'))
        if source_format:
            formats.append(source_format)

        info_dict_config = self._parse_config(config, video_id)
        formats.extend(info_dict_config['formats'])
        info_dict['_format_sort_fields'] = info_dict_config['_format_sort_fields']

        json_ld = self._search_json_ld(webpage, video_id, default={})

        if not cc_license:
            cc_license = self._search_regex(
                r'<link[^>]+rel=["\']license["\'][^>]+href=(["\'])(?P<license>(?:(?!\1).)+)\1',
                webpage, 'license', default=None, group='license')

        info_dict.update({
            'formats': formats,
            'timestamp': unified_timestamp(timestamp),
            'description': video_description,
            'webpage_url': url,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'license': cc_license,
        })

        return merge_dicts(info_dict, info_dict_config, json_ld)