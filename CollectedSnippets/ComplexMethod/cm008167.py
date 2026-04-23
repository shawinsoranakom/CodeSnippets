def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        host = mobj.group('host') or 'pornhub.com'
        video_id = mobj.group('id')

        self._login(host)
        self._set_age_cookies(host)

        def dl_webpage(platform):
            self._set_cookie(host, 'platform', platform)
            return self._download_webpage(
                f'https://www.{host}/view_video.php?viewkey={video_id}',
                video_id, f'Downloading {platform} webpage')

        webpage = dl_webpage('pc')

        error_msg = self._html_search_regex(
            (r'(?s)<div[^>]+class=(["\'])(?:(?!\1).)*\b(?:removed|userMessageSection)\b(?:(?!\1).)*\1[^>]*>(?P<error>.+?)</div>',
             r'(?s)<section[^>]+class=["\']noVideo["\'][^>]*>(?P<error>.+?)</section>'),
            webpage, 'error message', default=None, group='error')
        if error_msg:
            error_msg = re.sub(r'\s+', ' ', error_msg)
            raise ExtractorError(
                f'PornHub said: {error_msg}',
                expected=True, video_id=video_id)

        if any(re.search(p, webpage) for p in (
                r'class=["\']geoBlocked["\']',
                r'>\s*This content is unavailable in your country')):
            self.raise_geo_restricted()

        # video_title from flashvars contains whitespace instead of non-ASCII (see
        # http://www.pornhub.com/view_video.php?viewkey=1331683002), not relying
        # on that anymore.
        title = self._html_search_meta(
            'twitter:title', webpage, default=None) or self._html_search_regex(
            (r'(?s)<h1[^>]+class=["\']title["\'][^>]*>(?P<title>.+?)</h1>',
             r'<div[^>]+data-video-title=(["\'])(?P<title>(?:(?!\1).)+)\1',
             r'shareTitle["\']\s*[=:]\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', group='title')

        video_urls = []
        video_urls_set = set()
        subtitles = {}

        flashvars = self._parse_json(
            self._search_regex(
                r'var\s+flashvars_\d+\s*=\s*({.+?});', webpage, 'flashvars', default='{}'),
            video_id)
        if flashvars:
            subtitle_url = url_or_none(flashvars.get('closedCaptionsFile'))
            if subtitle_url:
                subtitles.setdefault('en', []).append({
                    'url': subtitle_url,
                    'ext': 'srt',
                })
            thumbnail = flashvars.get('image_url')
            duration = int_or_none(flashvars.get('video_duration'))
            media_definitions = flashvars.get('mediaDefinitions')
            if isinstance(media_definitions, list):
                for definition in media_definitions:
                    if not isinstance(definition, dict):
                        continue
                    video_url = definition.get('videoUrl')
                    if not video_url or not isinstance(video_url, str):
                        continue
                    if video_url in video_urls_set:
                        continue
                    video_urls_set.add(video_url)
                    video_urls.append(
                        (video_url, int_or_none(definition.get('quality'))))
        else:
            thumbnail, duration = [None] * 2

        def extract_js_vars(webpage, pattern, default=NO_DEFAULT):
            assignments = self._search_regex(
                pattern, webpage, 'encoded url', default=default)
            if not assignments:
                return {}

            assignments = assignments.split(';')

            js_vars = {}

            def parse_js_value(inp):
                inp = re.sub(r'/\*(?:(?!\*/).)*?\*/', '', inp)
                if '+' in inp:
                    inps = inp.split('+')
                    return functools.reduce(
                        operator.concat, map(parse_js_value, inps))
                inp = inp.strip()
                if inp in js_vars:
                    return js_vars[inp]
                return remove_quotes(inp)

            for assn in assignments:
                assn = assn.strip()
                if not assn:
                    continue
                assn = re.sub(r'var\s+', '', assn)
                vname, value = assn.split('=', 1)
                js_vars[vname] = parse_js_value(value)
            return js_vars

        def add_video_url(video_url):
            v_url = url_or_none(video_url)
            if not v_url:
                return
            if v_url in video_urls_set:
                return
            video_urls.append((v_url, None))
            video_urls_set.add(v_url)

        def parse_quality_items(quality_items):
            q_items = self._parse_json(quality_items, video_id, fatal=False)
            if not isinstance(q_items, list):
                return
            for item in q_items:
                if isinstance(item, dict):
                    add_video_url(item.get('url'))

        if not video_urls:
            FORMAT_PREFIXES = ('media', 'quality', 'qualityItems')
            js_vars = extract_js_vars(
                webpage, r'(var\s+(?:{})_.+)'.format('|'.join(FORMAT_PREFIXES)),
                default=None)
            if js_vars:
                for key, format_url in js_vars.items():
                    if key.startswith(FORMAT_PREFIXES[-1]):
                        parse_quality_items(format_url)
                    elif any(key.startswith(p) for p in FORMAT_PREFIXES[:2]):
                        add_video_url(format_url)
            if not video_urls and re.search(
                    r'<[^>]+\bid=["\']lockedPlayer', webpage):
                raise ExtractorError(
                    f'Video {video_id} is locked', expected=True)

        if not video_urls:
            js_vars = extract_js_vars(
                dl_webpage('tv'), r'(var.+?mediastring.+?)</script>')
            add_video_url(js_vars['mediastring'])

        for mobj in re.finditer(
                r'<a[^>]+\bclass=["\']downloadBtn\b[^>]+\bhref=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage):
            video_url = mobj.group('url')
            if video_url not in video_urls_set:
                video_urls.append((video_url, None))
                video_urls_set.add(video_url)

        upload_date = None
        formats = []

        def add_format(format_url, height=None):
            ext = determine_ext(format_url)
            if ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
                return
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                return
            if not height:
                height = int_or_none(self._search_regex(
                    r'(?P<height>\d+)[pP]?_\d+[kK]', format_url, 'height',
                    default=None))
            formats.append({
                'url': format_url,
                'format_id': format_field(height, None, '%dp'),
                'height': height,
            })

        for video_url, height in video_urls:
            if not upload_date:
                upload_date = self._search_regex(
                    r'/(\d{6}/\d{2})/', video_url, 'upload data', default=None)
                if upload_date:
                    upload_date = upload_date.replace('/', '')
            if '/video/get_media' in video_url:
                medias = self._download_json(video_url, video_id, fatal=False)
                if isinstance(medias, list):
                    for media in medias:
                        if not isinstance(media, dict):
                            continue
                        video_url = url_or_none(media.get('videoUrl'))
                        if not video_url:
                            continue
                        height = int_or_none(media.get('quality'))
                        add_format(video_url, height)
                continue
            add_format(video_url)

        model_profile = self._search_json(
            r'var\s+MODEL_PROFILE\s*=', webpage, 'model profile', video_id, fatal=False)
        video_uploader = self._html_search_regex(
            r'(?s)From:&nbsp;.+?<(?:a\b[^>]+\bhref=["\']/(?:(?:user|channel)s|model|pornstar)/|span\b[^>]+\bclass=["\']username)[^>]+>(.+?)<',
            webpage, 'uploader', default=None) or model_profile.get('username')

        def extract_vote_count(kind, name):
            return self._extract_count(
                (rf'<span[^>]+\bclass="votes{kind}"[^>]*>([\d,\.]+)</span>',
                 rf'<span[^>]+\bclass=["\']votes{kind}["\'][^>]*\bdata-rating=["\'](\d+)'),
                webpage, name)

        view_count = self._extract_count(
            r'<span class="count">([\d,\.]+)</span> [Vv]iews', webpage, 'view')
        like_count = extract_vote_count('Up', 'like')
        dislike_count = extract_vote_count('Down', 'dislike')
        comment_count = self._extract_count(
            r'All Comments\s*<span>\(([\d,.]+)\)', webpage, 'comment')

        info = self._search_json_ld(webpage, video_id, default={})
        # description provided in JSON-LD is irrelevant
        info['description'] = None

        return merge_dicts({
            'id': video_id,
            'uploader': video_uploader,
            'uploader_id': remove_start(model_profile.get('modelProfileLink'), '/model/'),
            'upload_date': upload_date,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
            **traverse_obj(webpage, {
                'tags': ({find_elements(attr='data-label', value='tag')}, ..., {clean_html}),
                'categories': ({find_elements(attr='data-label', value='category')}, ..., {clean_html}),
                'cast': ({find_elements(attr='data-label', value='pornstar')}, ..., {clean_html}),
            }),
            'subtitles': subtitles,
            'http_headers': {'Referer': f'https://www.{host}/'},
        }, info)