def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://api.globovideos.com/videos/%s/playlist' % video_id,
            video_id)['videos'][0]
        if video.get('encrypted') is True:
            raise ExtractorError('This video is DRM protected.', expected=True)

        title = video['title']

        formats = []
        subtitles = {}
        for resource in video['resources']:
            resource_id = resource.get('_id')
            resource_url = resource.get('url')
            resource_type = resource.get('type')
            if not resource_url or (resource_type == 'media' and not resource_id) or resource_type not in ('subtitle', 'media'):
                continue

            if resource_type == 'subtitle':
                subtitles.setdefault(resource.get('language') or 'por', []).append({
                    'url': resource_url,
                })
                continue

            security = self._download_json(
                'http://security.video.globo.com/videos/%s/hash' % video_id,
                video_id, 'Downloading security hash for %s' % resource_id, query={
                    'player': 'desktop',
                    'version': '5.19.1',
                    'resource_id': resource_id,
                })

            security_hash = security.get('hash')
            if not security_hash:
                message = security.get('message')
                if message:
                    raise ExtractorError(
                        '%s returned error: %s' % (self.IE_NAME, message), expected=True)
                continue

            hash_code = security_hash[:2]
            padding = '%010d' % random.randint(1, 10000000000)
            if hash_code in ('04', '14'):
                received_time = security_hash[3:13]
                received_md5 = security_hash[24:]
                hash_prefix = security_hash[:23]
            elif hash_code in ('02', '12', '03', '13'):
                received_time = security_hash[2:12]
                received_md5 = security_hash[22:]
                padding += '1'
                hash_prefix = '05' + security_hash[:22]

            padded_sign_time = compat_str(int(received_time) + 86400) + padding
            md5_data = (received_md5 + padded_sign_time + '0xAC10FD').encode()
            signed_md5 = base64.urlsafe_b64encode(hashlib.md5(md5_data).digest()).decode().strip('=')
            signed_hash = hash_prefix + padded_sign_time + signed_md5
            signed_url = '%s?h=%s&k=html5&a=%s&u=%s' % (resource_url, signed_hash, 'F' if video.get('subscriber_only') else 'A', security.get('user') or '')

            if resource_id.endswith('m3u8') or resource_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    signed_url, resource_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif resource_id.endswith('mpd') or resource_url.endswith('.mpd'):
                formats.extend(self._extract_mpd_formats(
                    signed_url, resource_id, mpd_id='dash', fatal=False))
            elif resource_id.endswith('manifest') or resource_url.endswith('/manifest'):
                formats.extend(self._extract_ism_formats(
                    signed_url, resource_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'url': signed_url,
                    'format_id': 'http-%s' % resource_id,
                    'height': int_or_none(resource.get('height')),
                })

        self._sort_formats(formats)

        duration = float_or_none(video.get('duration'), 1000)
        uploader = video.get('channel')
        uploader_id = str_or_none(video.get('channel_id'))

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
            'subtitles': subtitles,
        }