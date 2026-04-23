def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        headers = std_headers.copy()
        if 'http_headers' in data:
            headers.update(data['http_headers'])
        if 'Referer' not in headers:
            headers['Referer'] = url

        mobj = re.match(self._VALID_URL, url).groupdict()
        video_id, unlisted_hash = mobj['id'], mobj.get('unlisted_hash')
        if unlisted_hash:
            return self._extract_from_api(video_id, unlisted_hash)

        orig_url = url
        is_pro = 'vimeopro.com/' in url
        if is_pro:
            # some videos require portfolio_id to be present in player url
            # https://github.com/ytdl-org/youtube-dl/issues/20070
            url = self._extract_url(url, self._download_webpage(url, video_id))
            if not url:
                url = 'https://vimeo.com/' + video_id
        elif any(p in url for p in ('play_redirect_hls', 'moogaloop.swf')):
            url = 'https://vimeo.com/' + video_id

        try:
            # Retrieve video webpage to extract further information
            webpage, urlh = self._download_webpage_handle(
                url, video_id, headers=headers)
            redirect_url = urlh.geturl()
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 403:
                errmsg = ee.cause.read()
                if b'Because of its privacy settings, this video cannot be played here' in errmsg:
                    raise ExtractorError(
                        'Cannot download embed-only video without embedding '
                        'URL. Please call youtube-dl with the URL of the page '
                        'that embeds this video.',
                        expected=True)
            raise

        if '//player.vimeo.com/video/' in url:
            config = self._search_json(
                r'\b(?:playerC|c)onfig\s*=', webpage, 'info section', video_id)
            if config.get('view') == 4:
                config = self._verify_player_video_password(
                    redirect_url, video_id, headers)
            info = self._parse_config(config, video_id)
            self._vimeo_sort_formats(info['formats'])
            return info

        if re.search(r'<form[^>]+?id="pw_form"', webpage):
            video_password = self._get_video_password()
            token, vuid = self._extract_xsrft_and_vuid(webpage)
            webpage = self._verify_video_password(
                redirect_url, video_id, video_password, token, vuid)

        vimeo_config = self._extract_vimeo_config(webpage, video_id, default=None)
        if vimeo_config:
            seed_status = vimeo_config.get('seed_status') or {}
            if seed_status.get('state') == 'failed':
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, seed_status['title']),
                    expected=True)

        cc_license = None
        timestamp = None
        video_description = None
        info_dict = {}

        channel_id = self._search_regex(
            r'vimeo\.com/channels/([^/]+)', url, 'channel id', default=None)
        if channel_id:
            config_url = self._html_search_regex(
                r'\bdata-config-url="([^"]+)"', webpage, 'config URL')
            video_description = clean_html(get_element_by_class('description', webpage))
            info_dict.update({
                'channel_id': channel_id,
                'channel_url': 'https://vimeo.com/channels/' + channel_id,
            })
        else:
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
                    'https://player.vimeo.com/player/%s' % feature_id,
                    {'force_feature_id': True}), 'Vimeo')

        if not video_description:
            video_description = self._html_search_meta(
                ['description', 'og:description', 'twitter:description'],
                webpage, default=None)
        if not video_description and is_pro:
            orig_webpage = self._download_webpage(
                orig_url, video_id,
                note='Downloading webpage for description',
                fatal=False)
            if orig_webpage:
                video_description = self._html_search_meta(
                    'description', orig_webpage, default=None)
        if not video_description:
            self._downloader.report_warning('Cannot find video description')

        if not timestamp:
            timestamp = self._search_regex(
                r'<time[^>]+datetime="([^"]+)"', webpage,
                'timestamp', default=None)

        formats = []

        source_format = self._extract_original_format(
            'https://vimeo.com/' + video_id, video_id, video.get('unlisted_hash'))
        if source_format:
            formats.append(source_format)

        info_dict_config = self._parse_config(config, video_id)
        formats.extend(info_dict_config['formats'])
        self._vimeo_sort_formats(formats)

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
            'license': cc_license,
        })

        return merge_dicts(info_dict, info_dict_config, json_ld)