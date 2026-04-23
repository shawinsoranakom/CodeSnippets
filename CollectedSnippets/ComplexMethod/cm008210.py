def _extract_original_format(self, url, video_id, unlisted_hash=None):
        # Original/source formats are only available when logged in
        if not self._is_logged_in:
            return None

        policy = self._configuration_arg('original_format_policy', ['auto'], ie_key=VimeoIE)[0]
        if policy == 'never':
            return None

        try:
            download_data = self._download_json(
                url, video_id, 'Loading download config JSON', query=filter_dict({
                    'action': 'load_download_config',
                    'unlisted_hash': unlisted_hash,
                }), headers={
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                })
        except ExtractorError as error:
            self.write_debug(f'Unable to load download config JSON: {error.cause}')
            download_data = None

        source_file = traverse_obj(download_data, ('source_file', {dict})) or {}
        download_url = traverse_obj(source_file, ('download_url', {url_or_none}))
        if download_url and not source_file.get('is_cold') and not source_file.get('is_defrosting'):
            source_name = source_file.get('public_name', 'Original')
            if self._is_valid_url(download_url, video_id, f'{source_name} video'):
                ext = (try_get(
                    source_file, lambda x: x['extension'],
                    str) or determine_ext(
                    download_url, None) or 'mp4').lower()
                return {
                    'url': download_url,
                    'ext': ext,
                    'width': int_or_none(source_file.get('width')),
                    'height': int_or_none(source_file.get('height')),
                    'filesize': parse_filesize(source_file.get('size')),
                    'format_id': source_name,
                    'quality': 1,
                }

        # Most web client API requests are subject to rate-limiting (429) when logged-in.
        # Requesting only the 'privacy' field is NOT rate-limited,
        # so first we should check if video even has 'download' formats available
        try:
            privacy_info = self._call_videos_api(
                video_id, unlisted_hash, force_client='web', query={'fields': 'privacy'})
        except ExtractorError as error:
            self.write_debug(f'Unable to download privacy info: {error.cause}')
            return None

        if not traverse_obj(privacy_info, ('privacy', 'download', {bool})):
            msg = f'{video_id}: Vimeo says this video is not downloadable'
            if policy != 'always':
                self.write_debug(
                    f'{msg}, so yt-dlp is not attempting to extract the original/source format. '
                    f'To try anyways, use --extractor-args "vimeo:original_format_policy=always"')
                return None
            self.write_debug(f'{msg}; attempting to extract original/source format anyways')

        original_response = self._call_videos_api(
            video_id, unlisted_hash, force_client='web', query={'fields': 'download'}, fatal=False)
        for download_data in traverse_obj(original_response, ('download', ..., {dict})):
            download_url = download_data.get('link')
            if not download_url or download_data.get('quality') != 'source':
                continue
            ext = determine_ext(parse_qs(download_url).get('filename', [''])[0].lower(), default_ext=None)
            if not ext:
                urlh = self._request_webpage(
                    HEADRequest(download_url), video_id, fatal=False, note='Determining source extension')
                ext = urlh and urlhandle_detect_ext(urlh)
            return {
                'url': download_url,
                'ext': ext or 'unknown_video',
                'format_id': download_data.get('public_name', 'Original'),
                'width': int_or_none(download_data.get('width')),
                'height': int_or_none(download_data.get('height')),
                'fps': int_or_none(download_data.get('fps')),
                'filesize': int_or_none(download_data.get('size')),
                'quality': 1,
            }