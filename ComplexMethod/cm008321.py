def _extract_twitch_m3u8_formats(self, path, video_id, token, signature, live_from_start=False):
        try:
            formats = self._extract_m3u8_formats(
                f'{self._USHER_BASE}/{path}/{video_id}.m3u8', video_id, 'mp4', query={
                    'allow_source': 'true',
                    'allow_audio_only': 'true',
                    'allow_spectre': 'true',
                    'p': random.randint(1000000, 10000000),
                    'platform': 'web',
                    'player': 'twitchweb',
                    'supported_codecs': 'av1,h265,h264',
                    'playlist_include_framerate': 'true',
                    'sig': signature,
                    'token': token,
                })
        except ExtractorError as e:
            if (
                not isinstance(e.cause, HTTPError)
                or e.cause.status != 403
                or e.cause.response.get_header('content-type') != 'application/json'
            ):
                raise

            error_info = traverse_obj(e.cause.response.read(), ({json.loads}, 0, {dict})) or {}
            if error_info.get('error_code') in ('vod_manifest_restricted', 'unauthorized_entitlements'):
                common_msg = 'access to this subscriber-only content'
                if self._get_cookies('https://gql.twitch.tv').get('auth-token'):
                    raise ExtractorError(f'Your account does not have {common_msg}', expected=True)
                self.raise_login_required(f'You must be logged into an account that has {common_msg}')

            if error_msg := join_nonempty('error_code', 'error', from_dict=error_info, delim=': '):
                raise ExtractorError(error_msg, expected=True)
            raise

        for fmt in formats:
            if fmt.get('vcodec') and fmt['vcodec'].startswith('av01'):
                # mpegts does not yet have proper support for av1
                fmt.setdefault('downloader_options', {}).update({'ffmpeg_args_out': ['-f', 'mp4']})
            if live_from_start:
                fmt.setdefault('downloader_options', {}).update({'ffmpeg_args': ['-live_start_index', '0']})
                fmt['is_from_start'] = True

        return formats