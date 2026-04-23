def _extract_info_dict(self, info, full_title=None, secret_token=None, extract_flat=False):
        track_id = str(info['id'])

        format_urls = set()
        formats = []
        has_drm = False
        query = {'client_id': self._CLIENT_ID}
        if secret_token:
            query['secret_token'] = secret_token

        if not extract_flat and info.get('downloadable') and info.get('has_downloads_left'):
            try:
                # Do not use _call_api(); HTTP Error codes have different meanings for this request
                download_data = self._download_json(
                    f'{self._API_V2_BASE}tracks/{track_id}/download', track_id,
                    'Downloading original download format info JSON', query=query, headers=self._HEADERS)
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                    self.report_warning(
                        'Original download format is only available '
                        f'for registered users. {self._login_hint()}')
                elif isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    self.write_debug('Original download format is not available for this client')
                else:
                    self.report_warning(e.msg)
                download_data = None

            if redirect_url := traverse_obj(download_data, ('redirectUri', {url_or_none})):
                urlh = self._request_webpage(
                    HEADRequest(redirect_url), track_id, 'Checking original download format availability',
                    'Original download format is not available', fatal=False)
                if urlh:
                    format_url = urlh.url
                    format_urls.add(format_url)
                    formats.append({
                        'format_id': 'download',
                        'ext': urlhandle_detect_ext(urlh),
                        'filesize': int_or_none(urlh.headers.get('Content-Length')),
                        'url': format_url,
                        'quality': 10,
                        'format_note': 'Original',
                        'vcodec': 'none',
                    })

        def invalid_url(url):
            return not url or url in format_urls

        # New API
        for t in traverse_obj(info, ('media', 'transcodings', lambda _, v: url_or_none(v['url']) and v['preset'])):
            if extract_flat:
                break
            format_url = t['url']
            preset = t['preset']
            preset_base = preset.partition('_')[0]

            protocol = traverse_obj(t, ('format', 'protocol', {str})) or 'http'
            if protocol.startswith(('ctr-', 'cbc-')):
                has_drm = True
                continue
            if protocol == 'progressive':
                protocol = 'http'
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            if protocol == 'encrypted-hls' or '/encrypted-hls' in format_url:
                protocol = 'hls-aes'

            short_identifier = f'{protocol}_{preset_base}'
            if preset_base == 'abr':
                self.write_debug(f'Skipping broken "{short_identifier}" format')
                continue
            if not self._is_requested(short_identifier):
                self.write_debug(f'"{short_identifier}" is not a requested format, skipping')
                continue

            # XXX: if not extract_flat, 429 error must be caught where _extract_info_dict is called
            stream_url = traverse_obj(self._call_api(
                format_url, track_id, f'Downloading {short_identifier} format info JSON',
                query=query, headers=self._HEADERS), ('url', {url_or_none}))
            if invalid_url(stream_url):
                continue
            format_urls.add(stream_url)

            mime_type = traverse_obj(t, ('format', 'mime_type', {str}))
            codec = self._search_regex(r'codecs="([^"]+)"', mime_type, 'codec', default=None)
            ext = {
                'mp4a': 'm4a',
                'opus': 'opus',
            }.get(codec[:4] if codec else None) or mimetype2ext(mime_type, default=None)
            if not ext or ext == 'm3u8':
                ext = preset_base

            is_premium = t.get('quality') == 'hq'
            abr = int_or_none(
                self._search_regex(r'(\d+)k$', preset, 'abr', default=None)
                or self._search_regex(r'\.(\d+)\.(?:opus|mp3)[/?]', stream_url, 'abr', default=None)
                or (256 if (is_premium and 'aac' in preset) else None))

            is_preview = (t.get('snipped')
                          or '/preview/' in format_url
                          or re.search(r'/(?:preview|playlist)/0/30/', stream_url))

            formats.append({
                'format_id': join_nonempty(protocol, preset, is_preview and 'preview', delim='_'),
                'url': stream_url,
                'ext': ext,
                'acodec': codec,
                'vcodec': 'none',
                'abr': abr,
                'protocol': 'm3u8_native' if protocol in ('hls', 'hls-aes') else 'http',
                'container': 'm4a_dash' if ext == 'm4a' else None,
                'quality': 5 if is_premium else 0 if (abr and abr >= 160) else -1,
                'format_note': 'Premium' if is_premium else None,
                'preference': -10 if is_preview else None,
            })

        if not formats:
            if has_drm:
                self.report_drm(track_id)
            if info.get('policy') == 'BLOCK':
                self.raise_geo_restricted(metadata_available=True)

        user = info.get('user') or {}

        thumbnails = []
        artwork_url = info.get('artwork_url')
        thumbnail = artwork_url or user.get('avatar_url')
        if url_or_none(thumbnail):
            if mobj := re.search(self._IMAGE_REPL_RE, thumbnail):
                for image_id, size in self._ARTWORK_MAP.items():
                    # Soundcloud serves JPEG regardless of URL's ext *except* for "original" thumb
                    ext = mobj.group('ext') if image_id == 'original' else 'jpg'
                    i = {
                        'id': image_id,
                        'url': re.sub(self._IMAGE_REPL_RE, f'-{image_id}.{ext}', thumbnail),
                    }
                    if image_id == 'tiny' and not artwork_url:
                        size = 18
                    elif image_id == 'original':
                        i['preference'] = 10
                    if size:
                        i.update({
                            'width': size,
                            'height': size,
                        })
                    thumbnails.append(i)
            else:
                thumbnails = [{'url': thumbnail}]

        def extract_count(key):
            return int_or_none(info.get(f'{key}_count'))

        return {
            'id': track_id,
            'uploader': user.get('username'),
            'uploader_id': str_or_none(user.get('id')) or user.get('permalink'),
            'uploader_url': user.get('permalink_url'),
            'timestamp': unified_timestamp(info.get('created_at')),
            'title': info.get('title'),
            'track': info.get('title'),
            'description': info.get('description'),
            'thumbnails': thumbnails,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': extract_count('favoritings') or extract_count('likes'),
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genres': traverse_obj(info, ('genre', {str}, filter, all, filter)),
            'tags': traverse_obj(info, ('tag_list', {self._TAGS_RE.findall}, ..., ..., filter)),
            'artists': traverse_obj(info, ('publisher_metadata', 'artist', {str}, filter, all, filter)),
            'formats': formats if not extract_flat else None,
        }