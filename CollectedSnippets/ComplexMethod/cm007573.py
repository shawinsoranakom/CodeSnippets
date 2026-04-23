def _real_extract(self, url):
        host, video_id = self._match_valid_url(url).group('host', 'id')

        url = 'https://%s/%s' % (
            host,
            'embed-%s.html' % video_id if host in ('govid.me', 'vidlo.us') else video_id)
        webpage = self._download_webpage(url, video_id)
        container_div = get_element_by_id('container', webpage) or webpage
        if self._search_regex(
                r'>This server is in maintenance mode\.', container_div,
                'maint error', group=0, default=None):
            raise ExtractorError(clean_html(container_div), expected=True)
        if self._search_regex(
                self._FILE_NOT_FOUND_REGEXES, container_div,
                'missing video error', group=0, default=None):
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        fields = self._hidden_inputs(webpage)

        if fields.get('op') == 'download1':
            countdown = int_or_none(self._search_regex(
                r'<span id="countdown_str">(?:[Ww]ait)?\s*<span id="cxc">(\d+)</span>\s*(?:seconds?)?</span>',
                webpage, 'countdown', default=None))
            if countdown:
                self._sleep(countdown, video_id)

            webpage = self._download_webpage(
                url, video_id, 'Downloading video page',
                data=urlencode_postdata(fields), headers={
                    'Referer': url,
                    'Content-type': 'application/x-www-form-urlencoded',
                })

        title = (
            self._search_regex(self._TITLE_REGEXES, webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or video_id).strip()

        obf_code = True
        while obf_code:
            for regex, func in (
                    (r'(?s)(?<!-)\b(eval\(function\(p,a,c,k,e,d\)\{(?:(?!</script>).)+\)\))',
                     decode_packed_codes),
                    (r'(ﾟ.+)', aa_decode)):
                obf_code = self._search_regex(regex, webpage, 'obfuscated code', default=None)
                if obf_code:
                    webpage = webpage.replace(obf_code, func(obf_code))
                    break

        jwplayer_data = self._find_jwplayer_data(
            webpage.replace(r'\'', '\''), video_id)
        result = self._parse_jwplayer_data(
            jwplayer_data, video_id, require_title=False,
            m3u8_id='hls', mpd_id='dash')

        if not traverse_obj(result, 'formats'):
            if jwplayer_data:
                self.report_warning(
                    'Failed to extract JWPlayer formats', video_id=video_id)
            urls = set()
            for regex in self._SOURCE_URL_REGEXES:
                for mobj in re.finditer(regex, webpage):
                    urls.add(mobj.group('url'))

            sources = self._search_regex(
                r'sources\s*:\s*(\[(?!{)[^\]]+\])', webpage, 'sources', default=None)
            urls.update(traverse_obj(sources, (T(lambda s: self._parse_json(s, video_id)), Ellipsis)))

            formats = []
            for video_url in traverse_obj(urls, (Ellipsis, T(url_or_none))):
                if determine_ext(video_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': 'sd',
                    })
            result = {'formats': formats}

        self._sort_formats(result['formats'])

        thumbnail = self._search_regex(
            self._THUMBNAIL_REGEXES, webpage, 'thumbnail', default=None)

        if not (title or result.get('title')):
            title = self._generic_title(url) or video_id

        return merge_dicts(result, {
            'id': video_id,
            'title': title or None,
            'thumbnail': thumbnail,
            'http_headers': {'Referer': url}
        })