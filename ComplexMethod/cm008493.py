def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id, host = mobj.group('id', 'host')
        for display_id_key in ('display_id', 'display_id_2'):
            if display_id_key in mobj.groupdict():
                display_id = mobj.group(display_id_key)
                if display_id:
                    break
        else:
            display_id = video_id

        webpage = self._download_webpage(url, display_id)
        inputs = self._hidden_inputs(webpage)
        query = {}

        # check for MovieFap-style config
        cfg_url = self._proto_relative_url(self._html_search_regex(
            self._CONFIG_REGEX, webpage, 'flashvars.config', default=None,
            group='url'), 'http:')

        if not cfg_url:
            cfg_url = inputs.get('config')

        # check for TNAFlix-style config
        if not cfg_url and inputs.get('vkey') and inputs.get('nkey'):
            cfg_url = f'http://cdn-fck.{host}.com/{host}/{inputs["vkey"]}.fid'
            query.update({
                'key': inputs['nkey'],
                'VID': video_id,
                'premium': '1',
                'vip': '1',
                'alpha': '',
            })

        formats, json_ld = [], {}

        # TNAFlix and MovieFap extraction
        if cfg_url:
            cfg_xml = self._download_xml(
                cfg_url, display_id, 'Downloading metadata',
                transform_source=fix_xml_ampersands, headers={'Referer': url}, query=query)

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

            thumbnails = self._extract_thumbnails(cfg_xml) or []
            thumbnails.append({
                'url': self._proto_relative_url(xpath_text(cfg_xml, './startThumb', 'thumbnail'), 'http:'),
            })

        # check for EMPFlix-style JSON and extract
        else:
            player = self._download_json(
                f'http://www.{host}.com/ajax/video-player/{video_id}', video_id,
                headers={'Referer': url}).get('html', '')
            for mobj in re.finditer(r'<source src="(?P<src>[^"]+)"', player):
                video_url = mobj.group('src')
                height = self._search_regex(r'-(\d+)p\.', url_basename(video_url), 'height', default=None)
                formats.append({
                    'url': self._proto_relative_url(video_url, 'http:'),
                    'ext': url_basename(video_url).split('.')[-1],
                    'height': int_or_none(height),
                    'format_id': f'{height}p' if height else url_basename(video_url).split('.')[0],
                })
            thumbnail = self._proto_relative_url(self._search_regex(
                r'data-poster="([^"]+)"', player, 'thumbnail', default=None), 'http:')
            thumbnails = [{'url': thumbnail}] if thumbnail else None
            json_ld = self._search_json_ld(webpage, display_id, default={})

        def extract_field(pattern, name):
            return self._html_search_regex(pattern, webpage, name, default=None) if pattern else None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': (extract_field(self._TITLE_REGEX, 'title')
                      or self._og_search_title(webpage, default=None)
                      or json_ld.get('title')),
            'description': extract_field(self._DESCRIPTION_REGEX, 'description') or json_ld.get('description'),
            'thumbnails': thumbnails,
            'duration': parse_duration(
                self._html_search_meta('duration', webpage, 'duration', default=None)) or json_ld.get('duration'),
            'age_limit': self._rta_search(webpage) or 18,
            'uploader': extract_field(self._UPLOADER_REGEX, 'uploader') or json_ld.get('uploader'),
            'view_count': str_to_int(extract_field(self._VIEW_COUNT_REGEX, 'view count')),
            'comment_count': str_to_int(extract_field(self._COMMENT_COUNT_REGEX, 'comment count')),
            'average_rating': float_or_none(extract_field(self._AVERAGE_RATING_REGEX, 'average rating')),
            'categories': list(map(str.strip, (extract_field(self._CATEGORIES_REGEX, 'categories') or '').split(','))),
            'formats': formats,
        }