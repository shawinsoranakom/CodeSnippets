def _real_extract(self, url):
        # A different video ID (data-video-id) is hidden in the page but
        # never seems to be used
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        url = 'http://www.youporn.com/watch/%s' % (video_id,)
        webpage = self._download_webpage(
            url, video_id, headers={'Cookie': 'age_verified=1'})

        watchable = self._search_regex(
            r'''(<div\s[^>]*\bid\s*=\s*('|")?watch-container(?(2)\2|(?!-)\b)[^>]*>)''',
            webpage, 'watchability', default=None)
        if not watchable:
            msg = re.split(r'\s{4}', clean_html(get_element_by_id(
                'mainContent', webpage)) or '')[0]
            raise ExtractorError(
                ('%s says: %s' % (self.IE_NAME, msg))
                if msg else 'Video unavailable: no reason found',
                expected=True)
        # internal ID ?
        # video_id = extract_attributes(watchable).get('data-video-id')

        playervars = self._search_json(
            r'\bplayervars\s*:', webpage, 'playervars', video_id)

        def get_fmt(x):
            v_url = url_or_none(x.get('videoUrl'))
            if v_url:
                x['videoUrl'] = v_url
                return (x['format'], x)

        defs_by_format = dict(traverse_obj(playervars, (
            'mediaDefinitions', lambda _, v: v.get('format'), T(get_fmt))))

        def get_format_data(f):
            if f not in defs_by_format:
                return []
            return self._download_json(
                defs_by_format[f]['videoUrl'], video_id, '{0}-formats'.format(f))

        formats = []
        # Try to extract only the actual master m3u8 first, avoiding the duplicate single resolution "master" m3u8s
        for hls_url in traverse_obj(
                get_format_data('hls'),
                (lambda _, v: not isinstance(v['defaultQuality'], bool), 'videoUrl'),
                (Ellipsis, 'videoUrl')):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', fatal=False, m3u8_id='hls',
                entry_protocol='m3u8_native'))

        for f in traverse_obj(get_format_data('mp4'), (
                lambda _, v: v.get('videoUrl'), {
                    'url': ('videoUrl', T(url_or_none)),
                    'filesize': ('videoSize', T(int_or_none)),
                    'height': ('quality', T(int_or_none)),
                }, T(lambda x: x.get('videoUrl') and x))):
            # Video URL's path looks like this:
            #  /201012/17/505835/720p_1500k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            #  /201012/17/505835/vl_240p_240k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            #  /videos/201703/11/109285532/1080P_4000K_109285532.mp4
            # We will benefit from it by extracting some metadata
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', f['videoUrl'])
            if mobj:
                if not f.get('height'):
                    f['height'] = int(mobj.group('height'))
                f['tbr'] = int(mobj.group('bitrate'))
                f['format_id'] = '%dp-%dk' % (f['height'], f['tbr'])
            formats.append(f)
        self._sort_formats(formats)

        title = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']watchVideoTitle[^>]+>(.+?)</div>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'title', webpage, fatal=True)

        description = self._html_search_regex(
            r'(?s)<div[^>]+\bid=["\']description["\'][^>]*>(.+?)</div>',
            webpage, 'description',
            default=None) or self._og_search_description(
            webpage, default=None)
        thumbnail = self._search_regex(
            r'(?:imageurl\s*=|poster\s*:)\s*(["\'])(?P<thumbnail>.+?)\1',
            webpage, 'thumbnail', fatal=False, group='thumbnail')
        duration = traverse_obj(playervars, ('duration', T(int_or_none)))
        if duration is None:
            duration = int_or_none(self._html_search_meta(
                'video:duration', webpage, 'duration', fatal=False))

        uploader = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']submitByLink["\'][^>]*>(.+?)</div>',
            webpage, 'uploader', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            (r'UPLOADED:\s*<span>([^<]+)',
             r'Date\s+[Aa]dded:\s*<span>([^<]+)',
             r'''(?s)<div[^>]+class=["']videoInfo(?:Date|Time)\b[^>]*>(.+?)</div>''',
             r'(?s)<label\b[^>]*>Uploaded[^<]*</label>\s*<span\b[^>]*>(.+?)</span>'),
            webpage, 'upload date', fatal=False))

        age_limit = self._rta_search(webpage)

        view_count = None
        views = self._search_regex(
            r'(<div\s[^>]*\bdata-value\s*=[^>]+>)\s*<label>Views:</label>',
            webpage, 'views', default=None)
        if views:
            view_count = parse_count(extract_attributes(views).get('data-value'))
        comment_count = parse_count(self._search_regex(
            r'>All [Cc]omments? \(([\d,.]+)\)',
            webpage, 'comment count', default=None))

        def extract_tag_box(regex, title):
            tag_box = self._search_regex(regex, webpage, title, default=None)
            if not tag_box:
                return []
            return re.findall(r'<a[^>]+href=[^>]+>([^<]+)', tag_box)

        categories = extract_tag_box(
            r'(?s)Categories:.*?</[^>]+>(.+?)</div>', 'categories')
        tags = extract_tag_box(
            r'(?s)Tags:.*?</div>\s*<div[^>]+class=["\']tagBoxContent["\'][^>]*>(.+?)</div>',
            'tags')

        data = self._search_json_ld(webpage, video_id, expected_type='VideoObject', fatal=False) or {}
        data.pop('url', None)

        result = merge_dicts(data, {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'upload_date': upload_date,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
        })
        # Remove promotional non-description
        if result.get('description', '').startswith(
                'Watch %s online' % (result['title'],)):
            del result['description']
        return result