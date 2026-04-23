def _extract_info_dict(self, info, full_title=None, secret_token=None):
        track_id = compat_str(info['id'])
        title = info['title']

        format_urls = set()
        formats = []
        query = {'client_id': self._CLIENT_ID}
        if secret_token:
            query['secret_token'] = secret_token

        if info.get('downloadable') and info.get('has_downloads_left'):
            download_url = update_url_query(
                self._API_V2_BASE + 'tracks/' + track_id + '/download', query)
            redirect_url = (self._download_json(download_url, track_id, fatal=False) or {}).get('redirectUri')
            if redirect_url:
                urlh = self._request_webpage(
                    HEADRequest(redirect_url), track_id, fatal=False)
                if urlh:
                    format_url = urlh.geturl()
                    format_urls.add(format_url)
                    formats.append({
                        'format_id': 'download',
                        'ext': urlhandle_detect_ext(urlh) or 'mp3',
                        'filesize': int_or_none(urlh.headers.get('Content-Length')),
                        'url': format_url,
                        'preference': 10,
                    })

        def invalid_url(url):
            return not url or url in format_urls

        def add_format(f, protocol, is_preview=False):
            mobj = re.search(r'\.(?P<abr>\d+)\.(?P<ext>[0-9a-z]{3,4})(?=[/?])', stream_url)
            if mobj:
                for k, v in mobj.groupdict().items():
                    if not f.get(k):
                        f[k] = v
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            ext = f.get('ext')
            if ext == 'aac':
                f['abr'] = '256'
            for k in ('ext', 'abr'):
                v = f.get(k)
                if v:
                    format_id_list.append(v)
            preview = is_preview or re.search(r'/(?:preview|playlist)/0/30/', f['url'])
            if preview:
                format_id_list.append('preview')
            abr = f.get('abr')
            if abr:
                f['abr'] = int(abr)
            if protocol == 'hls':
                protocol = 'm3u8' if ext == 'aac' else 'm3u8_native'
            else:
                protocol = 'http'
            f.update({
                'format_id': '_'.join(format_id_list),
                'protocol': protocol,
                'preference': -10 if preview else None,
            })
            formats.append(f)

        # New API
        transcodings = try_get(
            info, lambda x: x['media']['transcodings'], list) or []
        for t in transcodings:
            if not isinstance(t, dict):
                continue
            format_url = url_or_none(t.get('url'))
            if not format_url:
                continue
            stream = self._download_json(
                format_url, track_id, query=query, fatal=False)
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if invalid_url(stream_url):
                continue
            format_urls.add(stream_url)
            stream_format = t.get('format') or {}
            protocol = stream_format.get('protocol')
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            ext = None
            preset = str_or_none(t.get('preset'))
            if preset:
                ext = preset.split('_')[0]
            if ext not in KNOWN_EXTENSIONS:
                ext = mimetype2ext(stream_format.get('mime_type'))
            add_format({
                'url': stream_url,
                'ext': ext,
            }, 'http' if protocol == 'progressive' else protocol,
                t.get('snipped') or '/preview/' in format_url)

        for f in formats:
            f['vcodec'] = 'none'

        if not formats and info.get('policy') == 'BLOCK':
            self.raise_geo_restricted()
        self._sort_formats(formats)

        user = info.get('user') or {}

        thumbnails = []
        artwork_url = info.get('artwork_url')
        thumbnail = artwork_url or user.get('avatar_url')
        if isinstance(thumbnail, compat_str):
            if re.search(self._IMAGE_REPL_RE, thumbnail):
                for image_id, size in self._ARTWORK_MAP.items():
                    i = {
                        'id': image_id,
                        'url': re.sub(self._IMAGE_REPL_RE, '-%s.jpg' % image_id, thumbnail),
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
            return int_or_none(info.get('%s_count' % key))

        return {
            'id': track_id,
            'uploader': user.get('username'),
            'uploader_id': str_or_none(user.get('id')) or user.get('permalink'),
            'uploader_url': user.get('permalink_url'),
            'timestamp': unified_timestamp(info.get('created_at')),
            'title': title,
            'description': info.get('description'),
            'thumbnails': thumbnails,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': extract_count('favoritings') or extract_count('likes'),
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genre': info.get('genre'),
            'formats': formats
        }