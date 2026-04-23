def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        for display_id_key in ('display_id', 'display_id_2'):
            if display_id_key in mobj.groupdict():
                display_id = mobj.group(display_id_key)
                if display_id:
                    break
        else:
            display_id = video_id

        webpage = self._download_webpage(url, display_id)

        cfg_url = self._proto_relative_url(self._html_search_regex(
            self._CONFIG_REGEX, webpage, 'flashvars.config', default=None,
            group='url'), 'http:')

        if not cfg_url:
            inputs = self._hidden_inputs(webpage)
            cfg_url = ('https://cdn-fck.%sflix.com/%sflix/%s%s.fid?key=%s&VID=%s&premium=1&vip=1&alpha'
                       % (self._HOST, self._HOST, inputs['vkey'], self._VKEY_SUFFIX, inputs['nkey'], video_id))

        cfg_xml = self._download_xml(
            cfg_url, display_id, 'Downloading metadata',
            transform_source=fix_xml_ampersands, headers={'Referer': url})

        formats = []

        def extract_video_url(vl):
            # Any URL modification now results in HTTP Error 403: Forbidden
            return unescapeHTML(vl.text)

        video_link = cfg_xml.find('./videoLink')
        if video_link is not None:
            formats.append({
                'url': extract_video_url(video_link),
                'ext': xpath_text(cfg_xml, './videoConfig/type', 'type', default='flv'),
            })

        for item in cfg_xml.findall('./quality/item'):
            video_link = item.find('./videoLink')
            if video_link is None:
                continue
            res = item.find('res')
            format_id = None if res is None else res.text
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]', format_id, 'height', default=None))
            formats.append({
                'url': self._proto_relative_url(extract_video_url(video_link), 'http:'),
                'format_id': format_id,
                'height': height,
            })

        self._sort_formats(formats)

        thumbnail = self._proto_relative_url(
            xpath_text(cfg_xml, './startThumb', 'thumbnail'), 'http:')
        thumbnails = self._extract_thumbnails(cfg_xml)

        title = None
        if self._TITLE_REGEX:
            title = self._html_search_regex(
                self._TITLE_REGEX, webpage, 'title', default=None)
        if not title:
            title = self._og_search_title(webpage)

        age_limit = self._rta_search(webpage) or 18

        duration = parse_duration(self._html_search_meta(
            'duration', webpage, 'duration', default=None))

        def extract_field(pattern, name):
            return self._html_search_regex(pattern, webpage, name, default=None) if pattern else None

        description = extract_field(self._DESCRIPTION_REGEX, 'description')
        uploader = extract_field(self._UPLOADER_REGEX, 'uploader')
        view_count = str_to_int(extract_field(self._VIEW_COUNT_REGEX, 'view count'))
        comment_count = str_to_int(extract_field(self._COMMENT_COUNT_REGEX, 'comment count'))
        average_rating = float_or_none(extract_field(self._AVERAGE_RATING_REGEX, 'average rating'))

        categories_str = extract_field(self._CATEGORIES_REGEX, 'categories')
        categories = [c.strip() for c in categories_str.split(',')] if categories_str is not None else []

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'thumbnails': thumbnails,
            'duration': duration,
            'age_limit': age_limit,
            'uploader': uploader,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'categories': categories,
            'formats': formats,
        }