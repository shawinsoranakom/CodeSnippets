def _get_media_token(self, video_config, config, display_id=None):
        resource_id = config['resourceId']
        if resource_id in self._token_cache:
            tokens = self._token_cache[resource_id]
        else:
            tokens = self._token_cache[resource_id] = self.cache.load(self._CACHE_SECTION, resource_id) or {}

        media_token = tokens.get(self._MEDIA_TOKEN_KEY)
        if media_token and not self._jwt_is_expired(media_token):
            return media_token

        access_token = self._get_fresh_access_token(config, display_id)
        if not jwt_decode_hs256(access_token).get('accessMethods'):
            # MTVServices uses a custom AdobePass oauth flow which is incompatible with AdobePassIE
            mso_id = self.get_param('ap_mso')
            if not mso_id:
                raise ExtractorError(
                    'This video is only available for users of participating TV providers. '
                    'Use --ap-mso to specify Adobe Pass Multiple-system operator Identifier and pass '
                    'cookies from a browser session where you are signed-in to your provider.', expected=True)

            auth_suite_data = json.dumps(
                self._get_auth_suite_data(config), separators=(',', ':')).encode()
            callback_url = update_url_query(config['callbackURL'], {
                'authSuiteData': urllib.parse.quote(base64.b64encode(auth_suite_data).decode()),
                'mvpdCode': mso_id,
            })
            auth_url = self._call_auth_api(
                f'mvpd/{mso_id}/login', config, display_id,
                'Retrieving provider authentication URL',
                query={'callbackUrl': callback_url},
                headers={'Authorization': f'Bearer {access_token}'})['authenticationUrl']
            res = self._download_webpage_handle(auth_url, display_id, 'Downloading provider auth page')
            # XXX: The following "provider-specific code" likely only works if mso_id == Comcast_SSO
            # BEGIN provider-specific code
            redirect_url = self._search_json(
                r'initInterstitialRedirect\(', res[0], 'redirect JSON',
                display_id, transform_source=js_to_json)['continue']
            urlh = self._request_webpage(redirect_url, display_id, 'Requesting provider redirect page')
            authorization_code = parse_qs(urlh.url)['authorizationCode'][-1]
            # END provider-specific code
            self._call_auth_api(
                f'access/mvpd/{mso_id}', config, display_id,
                'Submitting authorization code to MTVNServices',
                query={'authorizationCode': authorization_code}, data=b'',
                headers={'Authorization': f'Bearer {access_token}'})
            access_token = self._get_fresh_access_token(config, display_id, force_refresh=True)

        tokens[self._MEDIA_TOKEN_KEY] = self._call_auth_api(
            'mediaToken', config, display_id, 'Fetching media token', data={
                'content': {('id' if k == 'videoId' else k): v for k, v in video_config.items()},
                'resourceId': resource_id,
            }, headers={'Authorization': f'Bearer {access_token}'})['mediaToken']

        self.cache.store(self._CACHE_SECTION, resource_id, tokens)
        return tokens[self._MEDIA_TOKEN_KEY]