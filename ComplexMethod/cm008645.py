def _extra_manifest_info(self, info, manifest_url):
        fragment_query = self._configuration_arg('fragment_query', [None], casesense=True)[0]
        if fragment_query is not None:
            info['extra_param_to_segment_url'] = (
                urllib.parse.urlparse(fragment_query).query or fragment_query
                or urllib.parse.urlparse(manifest_url).query or None)

        key_query = self._configuration_arg('key_query', [None], casesense=True)[0]
        if key_query is not None:
            info['extra_param_to_key_url'] = (
                urllib.parse.urlparse(key_query).query or key_query
                or urllib.parse.urlparse(manifest_url).query or None)

        def hex_or_none(value):
            return value if re.fullmatch(r'(0x)?[\da-f]+', value, re.IGNORECASE) else None

        info['hls_aes'] = traverse_obj(self._configuration_arg('hls_key', casesense=True), {
            'uri': (0, {url_or_none}), 'key': (0, {hex_or_none}), 'iv': (1, {hex_or_none}),
        }) or None

        variant_query = self._configuration_arg('variant_query', [None], casesense=True)[0]
        if variant_query is not None:
            query = urllib.parse.parse_qs(
                urllib.parse.urlparse(variant_query).query or variant_query
                or urllib.parse.urlparse(manifest_url).query)
            for fmt in self._downloader._get_formats(info):
                fmt['url'] = update_url_query(fmt['url'], query)

        # Attempt to detect live HLS or set VOD duration
        m3u8_format = next((f for f in self._downloader._get_formats(info)
                            if determine_protocol(f) == 'm3u8_native'), None)
        if m3u8_format:
            is_live = self._configuration_arg('is_live', [None])[0]
            if is_live is not None:
                info['live_status'] = 'not_live' if is_live == 'false' else 'is_live'
                return
            headers = m3u8_format.get('http_headers') or info.get('http_headers') or {}
            display_id = info.get('id')
            urlh = self._request_webpage(
                m3u8_format['url'], display_id, 'Checking m3u8 live status', errnote=False,
                headers={**headers, 'Accept-Encoding': 'identity'}, fatal=False)
            if urlh is False:
                return
            first_bytes = urlh.read(512)
            if not first_bytes.startswith(b'#EXTM3U'):
                return
            m3u8_doc = self._webpage_read_content(
                urlh, urlh.url, display_id, prefix=first_bytes, fatal=False, errnote=False)
            if not m3u8_doc:
                return
            duration = self._parse_m3u8_vod_duration(m3u8_doc, display_id)
            if not duration:
                info['live_status'] = 'is_live'
            info['duration'] = info.get('duration') or duration