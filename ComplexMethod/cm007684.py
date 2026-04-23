def _real_extract(self, url):
        video_id = self._match_id(url)
        video_page = self._download_webpage(url, video_id)

        if 'videa.hu/player' in url:
            player_url = url
            player_page = video_page
        else:
            player_url = self._search_regex(
                r'<iframe.*?src="(/player\?[^"]+)"', video_page, 'player url')
            player_url = urljoin(url, player_url)
            player_page = self._download_webpage(player_url, video_id)

        nonce = self._search_regex(
            r'_xt\s*=\s*"([^"]+)"', player_page, 'nonce')
        l = nonce[:32]
        s = nonce[32:]
        result = ''
        for i in range(0, 32):
            result += s[i - (self._STATIC_SECRET.index(l[i]) - 31)]

        query = parse_qs(player_url)
        random_seed = ''.join(compat_random_choices(string.ascii_letters + string.digits, k=8))
        query['_s'] = random_seed
        query['_t'] = result[:16]

        b64_info, handle = self._download_webpage_handle(
            'http://videa.hu/player/xml', video_id, query=query)
        if b64_info.startswith('<?xml'):
            info = self._parse_xml(b64_info, video_id)
        else:
            key = result[16:] + random_seed + handle.headers['x-videa-xs']
            info = self._parse_xml(self.rc4(
                compat_b64decode(b64_info), key), video_id)

        video = xpath_element(info, './video', 'video')
        if video is None:
            raise ExtractorError(xpath_element(
                info, './error', fatal=True), expected=True)
        sources = xpath_element(
            info, './video_sources', 'sources', fatal=True)
        hash_values = xpath_element(
            info, './hash_values', 'hash values', fatal=False)

        title = xpath_text(video, './title', fatal=True)

        formats = []
        for source in sources.findall('./video_source'):
            source_url = source.text
            source_name = source.get('name')
            source_exp = source.get('exp')
            if not (source_url and source_name):
                continue
            hash_value = (
                xpath_text(hash_values, 'hash_value_' + source_name)
                if hash_values is not None else None)
            if hash_value and source_exp:
                source_url = update_url_query(source_url, {
                    'md5': hash_value,
                    'expires': source_exp,
                })
            f = parse_codecs(source.get('codecs'))
            f.update({
                'url': self._proto_relative_url(source_url),
                'ext': mimetype2ext(source.get('mimetype')) or 'mp4',
                'format_id': source.get('name'),
                'width': int_or_none(source.get('width')),
                'height': int_or_none(source.get('height')),
            })
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = self._proto_relative_url(xpath_text(video, './poster_src'))

        age_limit = None
        is_adult = xpath_text(video, './is_adult_content', default=None)
        if is_adult:
            age_limit = 18 if is_adult == '1' else 0

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': int_or_none(xpath_text(video, './duration')),
            'age_limit': age_limit,
            'formats': formats,
        }