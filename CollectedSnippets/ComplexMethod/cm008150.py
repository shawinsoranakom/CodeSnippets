def _real_extract(self, url):
        channel, video_id = self._match_valid_url(url).group('artist', 'id')
        post = self._call_post_api(video_id)
        api_video_id = post['extension']['video']['videoId']
        availability = self._extract_availability(post)
        live_status = self._extract_live_status(post)
        video_info, formats = {}, []

        if live_status == 'is_upcoming':
            self.raise_no_formats('Livestream has not yet started', expected=True)

        elif live_status == 'is_live':
            video_info = self._call_api(
                f'/video/v1.3/lives/{api_video_id}/playInfo?preview.format=json&preview.version=v2',
                video_id, note='Downloading live JSON')
            playback = self._parse_json(video_info['lipPlayback'], video_id)
            m3u8_url = traverse_obj(playback, (
                'media', lambda _, v: v['protocol'] == 'HLS', 'path', {url_or_none}), get_all=False)
            # Live subtitles are not downloadable, but extract to silence "ignoring subs" warning
            formats, _ = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', live=True)

        elif live_status == 'post_live':
            if availability in ('premium_only', 'subscriber_only'):
                self.report_drm(video_id)
            self.raise_no_formats(
                'Livestream has ended and downloadable VOD is not available', expected=True)

        else:
            infra_video_id = post['extension']['video']['infraVideoId']
            in_key = self._call_api(
                f'/video/v1.1/vod/{api_video_id}/inKey?preview=false', video_id,
                data=b'{}', note='Downloading VOD API key')['inKey']

            video_info = self._download_json(
                f'https://global.apis.naver.com/rmcnmv/rmcnmv/vod/play/v2.0/{infra_video_id}',
                video_id, note='Downloading VOD JSON', query={
                    'key': in_key,
                    'sid': traverse_obj(post, ('extension', 'video', 'serviceId')) or '2070',
                    'pid': str(uuid.uuid4()),
                    'nonce': int(time.time() * 1000),
                    'devt': 'html5_pc',
                    'prv': 'Y' if post.get('membershipOnly') else 'N',
                    'aup': 'N',
                    'stpb': 'N',
                    'cpl': 'en',
                    'env': 'prod',
                    'lc': 'en',
                    'adi': '[{"adSystem":"null"}]',
                    'adu': '/',
                })

            formats = self._get_formats(video_info, video_id)
            has_drm = traverse_obj(video_info, ('meta', 'provider', 'name', {str.lower})) == 'drm'
            if has_drm and formats:
                self.report_warning(
                    'Requested content is DRM-protected, only a 30-second preview is available', video_id)
            elif has_drm and not formats:
                self.report_drm(video_id)

        return {
            'id': video_id,
            'channel': channel,
            'channel_url': f'https://weverse.io/{channel}',
            'formats': formats,
            'availability': availability,
            'live_status': live_status,
            **self._parse_post_meta(post),
            **NaverBaseIE.process_subtitles(video_info, self._get_subs),
        }