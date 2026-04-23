def _extract_from_url(self, url, video_id):
        webpage = self._download_webpage(
            url.replace('://m.facebook.com/', '://www.facebook.com/'), video_id)

        video_data = None

        def extract_video_data(instances):
            video_data = []
            for item in instances:
                if try_get(item, lambda x: x[1][0]) == 'VideoConfig':
                    video_item = item[2][0]
                    if video_item.get('video_id'):
                        video_data.append(video_item['videoData'])
            return video_data

        server_js_data = self._parse_json(self._search_regex(
            [r'handleServerJS\(({.+})(?:\);|,")', r'\bs\.handle\(({.+?})\);'],
            webpage, 'server js data', default='{}'), video_id, fatal=False)

        if server_js_data:
            video_data = extract_video_data(server_js_data.get('instances', []))

        def extract_from_jsmods_instances(js_data):
            if js_data:
                return extract_video_data(try_get(
                    js_data, lambda x: x['jsmods']['instances'], list) or [])

        def extract_dash_manifest(video, formats):
            dash_manifest = video.get('dash_manifest')
            if dash_manifest:
                formats.extend(self._parse_mpd_formats(
                    compat_etree_fromstring(compat_urllib_parse_unquote_plus(dash_manifest))))

        def process_formats(formats):
            # Downloads with browser's User-Agent are rate limited. Working around
            # with non-browser User-Agent.
            for f in formats:
                f.setdefault('http_headers', {})['User-Agent'] = 'facebookexternalhit/1.1'

            self._sort_formats(formats)

        def extract_relay_data(_filter):
            return self._parse_json(self._search_regex(
                r'handleWithCustomApplyEach\([^,]+,\s*({.*?%s.*?})\);' % _filter,
                webpage, 'replay data', default='{}'), video_id, fatal=False) or {}

        def extract_relay_prefetched_data(_filter):
            replay_data = extract_relay_data(_filter)
            for require in (replay_data.get('require') or []):
                if require[0] == 'RelayPrefetchedStreamCache':
                    return try_get(require, lambda x: x[3][1]['__bbox']['result']['data'], dict) or {}

        if not video_data:
            server_js_data = self._parse_json(self._search_regex([
                r'bigPipe\.onPageletArrive\(({.+?})\)\s*;\s*}\s*\)\s*,\s*["\']onPageletArrive\s+' + self._SUPPORTED_PAGLETS_REGEX,
                r'bigPipe\.onPageletArrive\(({.*?id\s*:\s*"%s".*?})\);' % self._SUPPORTED_PAGLETS_REGEX
            ], webpage, 'js data', default='{}'), video_id, js_to_json, False)
            video_data = extract_from_jsmods_instances(server_js_data)

        if not video_data:
            data = extract_relay_prefetched_data(
                r'"(?:dash_manifest|playable_url(?:_quality_hd)?)"\s*:\s*"[^"]+"')
            if data:
                entries = []

                def parse_graphql_video(video):
                    formats = []
                    q = qualities(['sd', 'hd'])
                    for (suffix, format_id) in [('', 'sd'), ('_quality_hd', 'hd')]:
                        playable_url = video.get('playable_url' + suffix)
                        if not playable_url:
                            continue
                        formats.append({
                            'format_id': format_id,
                            'quality': q(format_id),
                            'url': playable_url,
                        })
                    extract_dash_manifest(video, formats)
                    process_formats(formats)
                    v_id = video.get('videoId') or video.get('id') or video_id
                    info = {
                        'id': v_id,
                        'formats': formats,
                        'thumbnail': try_get(video, lambda x: x['thumbnailImage']['uri']),
                        'uploader_id': try_get(video, lambda x: x['owner']['id']),
                        'timestamp': int_or_none(video.get('publish_time')),
                        'duration': float_or_none(video.get('playable_duration_in_ms'), 1000),
                    }
                    description = try_get(video, lambda x: x['savable_description']['text'])
                    title = video.get('name')
                    if title:
                        info.update({
                            'title': title,
                            'description': description,
                        })
                    else:
                        info['title'] = description or 'Facebook video #%s' % v_id
                    entries.append(info)

                def parse_attachment(attachment, key='media'):
                    media = attachment.get(key) or {}
                    if media.get('__typename') == 'Video':
                        return parse_graphql_video(media)

                nodes = data.get('nodes') or []
                node = data.get('node') or {}
                if not nodes and node:
                    nodes.append(node)
                for node in nodes:
                    story = try_get(node, lambda x: x['comet_sections']['content']['story'], dict) or {}
                    attachments = try_get(story, [
                        lambda x: x['attached_story']['attachments'],
                        lambda x: x['attachments']
                    ], list) or []
                    for attachment in attachments:
                        attachment = try_get(attachment, lambda x: x['style_type_renderer']['attachment'], dict)
                        ns = try_get(attachment, lambda x: x['all_subattachments']['nodes'], list) or []
                        for n in ns:
                            parse_attachment(n)
                        parse_attachment(attachment)

                edges = try_get(data, lambda x: x['mediaset']['currMedia']['edges'], list) or []
                for edge in edges:
                    parse_attachment(edge, key='node')

                video = data.get('video') or {}
                if video:
                    attachments = try_get(video, [
                        lambda x: x['story']['attachments'],
                        lambda x: x['creation_story']['attachments']
                    ], list) or []
                    for attachment in attachments:
                        parse_attachment(attachment)
                    if not entries:
                        parse_graphql_video(video)

                return self.playlist_result(entries, video_id)

        if not video_data:
            m_msg = re.search(r'class="[^"]*uiInterstitialContent[^"]*"><div>(.*?)</div>', webpage)
            if m_msg is not None:
                raise ExtractorError(
                    'The video is not available, Facebook said: "%s"' % m_msg.group(1),
                    expected=True)
            elif any(p in webpage for p in (
                    '>You must log in to continue',
                    'id="login_form"',
                    'id="loginbutton"')):
                self.raise_login_required()

        if not video_data and '/watchparty/' in url:
            post_data = {
                'doc_id': 3731964053542869,
                'variables': json.dumps({
                    'livingRoomID': video_id,
                }),
            }

            prefetched_data = extract_relay_prefetched_data(r'"login_data"\s*:\s*{')
            if prefetched_data:
                lsd = try_get(prefetched_data, lambda x: x['login_data']['lsd'], dict)
                if lsd:
                    post_data[lsd['name']] = lsd['value']

            relay_data = extract_relay_data(r'\[\s*"RelayAPIConfigDefaults"\s*,')
            for define in (relay_data.get('define') or []):
                if define[0] == 'RelayAPIConfigDefaults':
                    self._api_config = define[2]

            living_room = self._download_json(
                urljoin(url, self._api_config['graphURI']), video_id,
                data=urlencode_postdata(post_data))['data']['living_room']

            entries = []
            for edge in (try_get(living_room, lambda x: x['recap']['watched_content']['edges']) or []):
                video = try_get(edge, lambda x: x['node']['video']) or {}
                v_id = video.get('id')
                if not v_id:
                    continue
                v_id = compat_str(v_id)
                entries.append(self.url_result(
                    self._VIDEO_PAGE_TEMPLATE % v_id,
                    self.ie_key(), v_id, video.get('name')))

            return self.playlist_result(entries, video_id)

        if not video_data:
            # Video info not in first request, do a secondary request using
            # tahoe player specific URL
            tahoe_data = self._download_webpage(
                self._VIDEO_PAGE_TAHOE_TEMPLATE % video_id, video_id,
                data=urlencode_postdata({
                    '__a': 1,
                    '__pc': self._search_regex(
                        r'pkg_cohort["\']\s*:\s*["\'](.+?)["\']', webpage,
                        'pkg cohort', default='PHASED:DEFAULT'),
                    '__rev': self._search_regex(
                        r'client_revision["\']\s*:\s*(\d+),', webpage,
                        'client revision', default='3944515'),
                    'fb_dtsg': self._search_regex(
                        r'"DTSGInitialData"\s*,\s*\[\]\s*,\s*{\s*"token"\s*:\s*"([^"]+)"',
                        webpage, 'dtsg token', default=''),
                }),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                })
            tahoe_js_data = self._parse_json(
                self._search_regex(
                    r'for\s+\(\s*;\s*;\s*\)\s*;(.+)', tahoe_data,
                    'tahoe js data', default='{}'),
                video_id, fatal=False)
            video_data = extract_from_jsmods_instances(tahoe_js_data)

        if not video_data:
            raise ExtractorError('Cannot parse data')

        if len(video_data) > 1:
            entries = []
            for v in video_data:
                video_url = v[0].get('video_url')
                if not video_url:
                    continue
                entries.append(self.url_result(urljoin(
                    url, video_url), self.ie_key(), v[0].get('video_id')))
            return self.playlist_result(entries, video_id)
        video_data = video_data[0]

        formats = []
        subtitles = {}
        for f in video_data:
            format_id = f['stream_type']
            if f and isinstance(f, dict):
                f = [f]
            if not f or not isinstance(f, list):
                continue
            for quality in ('sd', 'hd'):
                for src_type in ('src', 'src_no_ratelimit'):
                    src = f[0].get('%s_%s' % (quality, src_type))
                    if src:
                        preference = -10 if format_id == 'progressive' else 0
                        if quality == 'hd':
                            preference += 5
                        formats.append({
                            'format_id': '%s_%s_%s' % (format_id, quality, src_type),
                            'url': src,
                            'preference': preference,
                        })
            extract_dash_manifest(f[0], formats)
            subtitles_src = f[0].get('subtitles_src')
            if subtitles_src:
                subtitles.setdefault('en', []).append({'url': subtitles_src})
        if not formats:
            raise ExtractorError('Cannot find video formats')

        process_formats(formats)

        video_title = self._html_search_regex(
            r'<h2\s+[^>]*class="uiHeaderTitle"[^>]*>([^<]*)</h2>', webpage,
            'title', default=None)
        if not video_title:
            video_title = self._html_search_regex(
                r'(?s)<span class="fbPhotosPhotoCaption".*?id="fbPhotoPageCaption"><span class="hasCaption">(.*?)</span>',
                webpage, 'alternative title', default=None)
        if not video_title:
            video_title = self._html_search_meta(
                'description', webpage, 'title', default=None)
        if video_title:
            video_title = limit_length(video_title, 80)
        else:
            video_title = 'Facebook video #%s' % video_id
        uploader = clean_html(get_element_by_id(
            'fbPhotoPageAuthorName', webpage)) or self._search_regex(
            r'ownerName\s*:\s*"([^"]+)"', webpage, 'uploader',
            default=None) or self._og_search_title(webpage, fatal=False)
        timestamp = int_or_none(self._search_regex(
            r'<abbr[^>]+data-utime=["\'](\d+)', webpage,
            'timestamp', default=None))
        thumbnail = self._html_search_meta(['og:image', 'twitter:image'], webpage)

        view_count = parse_count(self._search_regex(
            r'\bviewCount\s*:\s*["\']([\d,.]+)', webpage, 'view count',
            default=None))

        info_dict = {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'uploader': uploader,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'subtitles': subtitles,
        }

        return info_dict