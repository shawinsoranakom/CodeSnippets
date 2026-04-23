def _extract_video_info(self, url, clip_id):
        client_location = url

        video = self._download_json(
            'http://vas.sim-technik.de/vas/live/v2/videos',
            clip_id, 'Downloading videos JSON', query={
                'access_token': self._TOKEN,
                'client_location': client_location,
                'client_name': self._CLIENT_NAME,
                'ids': clip_id,
            })[0]

        if not self.get_param('allow_unplayable_formats') and video.get('is_protected') is True:
            self.report_drm(clip_id)

        formats = []
        if self._ACCESS_ID:
            raw_ct = self._ENCRYPTION_KEY + clip_id + self._IV + self._ACCESS_ID
            protocols = self._download_json(
                self._V4_BASE_URL + 'protocols', clip_id,
                'Downloading protocols JSON',
                headers=self.geo_verification_headers(), query={
                    'access_id': self._ACCESS_ID,
                    'client_token': hashlib.sha1((raw_ct).encode()).hexdigest(),
                    'video_id': clip_id,
                }, fatal=False, expected_status=(403,)) or {}
            error = protocols.get('error') or {}
            if error.get('title') == 'Geo check failed':
                self.raise_geo_restricted(countries=['AT', 'CH', 'DE'])
            server_token = protocols.get('server_token')
            if server_token:
                urls = (self._download_json(
                    self._V4_BASE_URL + 'urls', clip_id, 'Downloading urls JSON', query={
                        'access_id': self._ACCESS_ID,
                        'client_token': hashlib.sha1((raw_ct + server_token + self._SUPPORTED_PROTOCOLS).encode()).hexdigest(),
                        'protocols': self._SUPPORTED_PROTOCOLS,
                        'server_token': server_token,
                        'video_id': clip_id,
                    }, fatal=False) or {}).get('urls') or {}
                for protocol, variant in urls.items():
                    source_url = variant.get('clear', {}).get('url')
                    if not source_url:
                        continue
                    if protocol == 'dash':
                        formats.extend(self._extract_mpd_formats(
                            source_url, clip_id, mpd_id=protocol, fatal=False))
                    elif protocol == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            source_url, clip_id, 'mp4', 'm3u8_native',
                            m3u8_id=protocol, fatal=False))
                    else:
                        formats.append({
                            'url': source_url,
                            'format_id': protocol,
                        })
        if not formats:
            source_ids = [str(source['id']) for source in video['sources']]

            client_id = self._SALT[:2] + hashlib.sha1(''.join([clip_id, self._SALT, self._TOKEN, client_location, self._SALT, self._CLIENT_NAME]).encode()).hexdigest()

            sources = self._download_json(
                f'http://vas.sim-technik.de/vas/live/v2/videos/{clip_id}/sources',
                clip_id, 'Downloading sources JSON', query={
                    'access_token': self._TOKEN,
                    'client_id': client_id,
                    'client_location': client_location,
                    'client_name': self._CLIENT_NAME,
                })
            server_id = sources['server_id']

            def fix_bitrate(bitrate):
                bitrate = int_or_none(bitrate)
                if not bitrate:
                    return None
                return (bitrate // 1000) if bitrate % 1000 == 0 else bitrate

            for source_id in source_ids:
                client_id = self._SALT[:2] + hashlib.sha1(''.join([self._SALT, clip_id, self._TOKEN, server_id, client_location, source_id, self._SALT, self._CLIENT_NAME]).encode()).hexdigest()
                urls = self._download_json(
                    f'http://vas.sim-technik.de/vas/live/v2/videos/{clip_id}/sources/url',
                    clip_id, 'Downloading urls JSON', fatal=False, query={
                        'access_token': self._TOKEN,
                        'client_id': client_id,
                        'client_location': client_location,
                        'client_name': self._CLIENT_NAME,
                        'server_id': server_id,
                        'source_ids': source_id,
                    })
                if not urls:
                    continue
                if urls.get('status_code') != 0:
                    raise ExtractorError('This video is unavailable', expected=True)
                urls_sources = urls['sources']
                if isinstance(urls_sources, dict):
                    urls_sources = urls_sources.values()
                for source in urls_sources:
                    source_url = source.get('url')
                    if not source_url:
                        continue
                    protocol = source.get('protocol')
                    mimetype = source.get('mimetype')
                    if mimetype == 'application/f4m+xml' or 'f4mgenerator' in source_url or determine_ext(source_url) == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            source_url, clip_id, f4m_id='hds', fatal=False))
                    elif mimetype == 'application/x-mpegURL':
                        formats.extend(self._extract_m3u8_formats(
                            source_url, clip_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    elif mimetype == 'application/dash+xml':
                        formats.extend(self._extract_mpd_formats(
                            source_url, clip_id, mpd_id='dash', fatal=False))
                    else:
                        tbr = fix_bitrate(source['bitrate'])
                        if protocol in ('rtmp', 'rtmpe'):
                            mobj = re.search(r'^(?P<url>rtmpe?://[^/]+)/(?P<path>.+)$', source_url)
                            if not mobj:
                                continue
                            path = mobj.group('path')
                            mp4colon_index = path.rfind('mp4:')
                            app = path[:mp4colon_index]
                            play_path = path[mp4colon_index:]
                            formats.append({
                                'url': '{}/{}'.format(mobj.group('url'), app),
                                'app': app,
                                'play_path': play_path,
                                'player_url': 'http://livepassdl.conviva.com/hf/ver/2.79.0.17083/LivePassModuleMain.swf',
                                'page_url': 'http://www.prosieben.de',
                                'tbr': tbr,
                                'ext': 'flv',
                                'format_id': join_nonempty('rtmp', tbr),
                            })
                        else:
                            formats.append({
                                'url': source_url,
                                'tbr': tbr,
                                'format_id': join_nonempty('http', tbr),
                            })

        return {
            'duration': float_or_none(video.get('duration')),
            'formats': formats,
        }