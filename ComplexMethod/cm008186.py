def _extract_mvpd_auth(self, url, video_id, requestor_id, resource, software_statement):
        mso_id = self.get_param('ap_mso')
        if mso_id:
            mso_info = MSO_INFO[mso_id]
        else:
            mso_info = {}

        def xml_text(xml_str, tag):
            return self._search_regex(
                f'<{tag}>(.+?)</{tag}>', xml_str, tag)

        def is_expired(token, date_ele):
            token_expires = unified_timestamp(re.sub(r'[_ ]GMT', '', xml_text(token, date_ele)))
            return token_expires and token_expires <= int(time.time())

        def post_form(form_page_res, note, data={}, validate_url=False):
            form_page, urlh = form_page_res
            post_url = self._html_search_regex(r'<form[^>]+action=(["\'])(?P<url>.+?)\1', form_page, 'post url', group='url')
            if not re.match(r'https?://', post_url):
                post_url = urllib.parse.urljoin(urlh.url, post_url)
            if validate_url:
                # This request is submitting credentials so we should validate it when possible
                url_parsed = urllib.parse.urlparse(post_url)
                expected_hostname = mso_info.get('login_hostname')
                if expected_hostname and expected_hostname != url_parsed.hostname:
                    raise ExtractorError(
                        f'Unexpected login URL hostname; expected "{expected_hostname}" but got '
                        f'"{url_parsed.hostname}". Aborting before submitting credentials')
                if url_parsed.scheme != 'https':
                    self.write_debug('Upgrading login URL scheme to https')
                    post_url = urllib.parse.urlunparse(url_parsed._replace(scheme='https'))
            form_data = self._hidden_inputs(form_page)
            form_data.update(data)
            return self._download_webpage_handle(
                post_url, video_id, note, data=urlencode_postdata(form_data), headers={
                    **self._get_mso_headers(mso_info),
                    'Content-Type': 'application/x-www-form-urlencoded',
                })

        def raise_mvpd_required():
            raise ExtractorError(
                'This video is only available for users of participating TV providers. '
                'Use --ap-mso to specify Adobe Pass Multiple-system operator Identifier '
                'and --ap-username and --ap-password or --netrc to provide account credentials.', expected=True)

        def extract_redirect_url(html, url=None, fatal=False):
            # TODO: eliminate code duplication with generic extractor and move
            # redirection code into _download_webpage_handle
            REDIRECT_REGEX = r'[0-9]{,2};\s*(?:URL|url)=\'?([^\'"]+)'
            redirect_url = self._search_regex(
                r'(?i)<meta\s+(?=(?:[a-z-]+="[^"]+"\s+)*http-equiv="refresh")'
                rf'(?:[a-z-]+="[^"]+"\s+)*?content="{REDIRECT_REGEX}',
                html, 'meta refresh redirect',
                default=NO_DEFAULT if fatal else None, fatal=fatal)
            if not redirect_url:
                return None
            if url:
                redirect_url = urllib.parse.urljoin(url, unescapeHTML(redirect_url))
            return redirect_url

        mvpd_headers = {
            'ap_42': 'anonymous',
            'ap_11': 'Linux i686',
            'ap_z': self._USER_AGENT,
            'User-Agent': self._USER_AGENT,
        }

        guid = xml_text(resource, 'guid') if '<' in resource else resource
        for _ in range(2):
            requestor_info = self.cache.load(self._MVPD_CACHE, requestor_id) or {}
            authn_token = requestor_info.get('authn_token')
            if authn_token and is_expired(authn_token, 'simpleTokenExpires'):
                authn_token = None
            if not authn_token:
                if not mso_id:
                    raise_mvpd_required()
                username, password = self._get_login_info('ap_username', 'ap_password', mso_id)
                if not username or not password:
                    raise_mvpd_required()

                device_info, urlh = self._download_json_handle(
                    'https://sp.auth.adobe.com/indiv/devices',
                    video_id, 'Registering device with Adobe',
                    data=json.dumps({'fingerprint': uuid.uuid4().hex}).encode(),
                    headers={'Content-Type': 'application/json; charset=UTF-8'})

                device_id = device_info['deviceId']
                mvpd_headers['pass_sfp'] = urlh.get_header('pass_sfp')
                mvpd_headers['Ap_21'] = device_id

                registration = self._download_json(
                    'https://sp.auth.adobe.com/o/client/register',
                    video_id, 'Registering client with Adobe',
                    data=json.dumps({'software_statement': software_statement}).encode(),
                    headers={'Content-Type': 'application/json; charset=UTF-8'})

                access_token = self._download_json(
                    'https://sp.auth.adobe.com/o/client/token', video_id,
                    'Obtaining access token', data=urlencode_postdata({
                        'grant_type': 'client_credentials',
                        'client_id': registration['client_id'],
                        'client_secret': registration['client_secret'],
                    }),
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    })['access_token']
                mvpd_headers['Authorization'] = f'Bearer {access_token}'

                reg_code = self._download_json(
                    f'https://sp.auth.adobe.com/reggie/v1/{requestor_id}/regcode',
                    video_id, 'Obtaining registration code',
                    data=urlencode_postdata({
                        'requestor': requestor_id,
                        'deviceId': device_id,
                        'format': 'json',
                    }),
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Authorization': f'Bearer {access_token}',
                    })['code']

                provider_redirect_page_res = self._download_webpage_handle(
                    self._SERVICE_PROVIDER_TEMPLATE % 'authenticate/saml', video_id,
                    'Downloading Provider Redirect Page', query={
                        'noflash': 'true',
                        'mso_id': mso_id,
                        'requestor_id': requestor_id,
                        'no_iframe': 'false',
                        'domain_name': 'adobe.com',
                        'redirect_url': url,
                        'reg_code': reg_code,
                    }, headers=self._get_mso_headers(mso_info))

                if mso_id == 'Comcast_SSO':
                    # Comcast page flow varies by video site and whether you
                    # are on Comcast's network.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    if 'automatically signing you in' in provider_redirect_page:
                        oauth_redirect_url = self._html_search_regex(
                            r'window\.location\s*=\s*[\'"]([^\'"]+)',
                            provider_redirect_page, 'oauth redirect')
                        self._download_webpage(
                            oauth_redirect_url, video_id, 'Confirming auto login')
                    elif 'automatically signed in with' in provider_redirect_page:
                        # Seems like comcast is rolling up new way of automatically signing customers
                        oauth_redirect_url = self._html_search_regex(
                            r'continue:\s*"(https://oauth\.xfinity\.com/oauth/authorize\?.+)"', provider_redirect_page,
                            'oauth redirect (signed)')
                        # Just need to process the request. No useful data comes back
                        self._download_webpage(oauth_redirect_url, video_id, 'Confirming auto login')
                    else:
                        if '<form name="signin"' in provider_redirect_page:
                            provider_login_page_res = provider_redirect_page_res
                        elif 'http-equiv="refresh"' in provider_redirect_page:
                            oauth_redirect_url = extract_redirect_url(
                                provider_redirect_page, fatal=True)
                            provider_login_page_res = self._download_webpage_handle(
                                oauth_redirect_url, video_id, self._DOWNLOADING_LOGIN_PAGE,
                                headers=self._get_mso_headers(mso_info))
                        else:
                            provider_login_page_res = post_form(
                                provider_redirect_page_res,
                                self._DOWNLOADING_LOGIN_PAGE)

                        mvpd_confirm_page_res = post_form(
                            provider_login_page_res, 'Logging in', {
                                mso_info['username_field']: username,
                                mso_info['password_field']: password,
                            }, validate_url=True)
                        mvpd_confirm_page, urlh = mvpd_confirm_page_res
                        if '<button class="submit" value="Resume">Resume</button>' in mvpd_confirm_page:
                            post_form(mvpd_confirm_page_res, 'Confirming Login')
                elif mso_id == 'Philo':
                    # Philo has very unique authentication method
                    self._request_webpage(
                        'https://idp.philo.com/auth/init/login_code', video_id,
                        'Requesting Philo auth code', data=json.dumps({
                            'ident': username,
                            'device': 'web',
                            'send_confirm_link': False,
                            'send_token': True,
                            'device_ident': f'web-{uuid.uuid4().hex}',
                            'include_login_link': True,
                        }).encode(), headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                        })

                    philo_code = getpass.getpass('Type auth code you have received [Return]: ')
                    self._request_webpage(
                        'https://idp.philo.com/auth/update/login_code', video_id,
                        'Submitting token', data=json.dumps({'token': philo_code}).encode(),
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                        })

                    mvpd_confirm_page_res = self._download_webpage_handle('https://idp.philo.com/idp/submit', video_id, 'Confirming Philo Login')
                    post_form(mvpd_confirm_page_res, 'Confirming Login')
                elif mso_id == 'Verizon':
                    # In general, if you're connecting from a Verizon-assigned IP,
                    # you will not actually pass your credentials.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    # From non-Verizon IP, still gave 'Please wait', but noticed N==Y; will need to try on Verizon IP
                    if 'Please wait ...' in provider_redirect_page and '\'N\'== "Y"' not in provider_redirect_page:
                        saml_redirect_url = self._html_search_regex(
                            r'self\.parent\.location=(["\'])(?P<url>.+?)\1',
                            provider_redirect_page,
                            'SAML Redirect URL', group='url')
                        saml_login_page = self._download_webpage(
                            saml_redirect_url, video_id,
                            'Downloading SAML Login Page')
                    elif 'Verizon FiOS - sign in' in provider_redirect_page:
                        # FXNetworks from non-Verizon IP
                        saml_login_page_res = post_form(
                            provider_redirect_page_res, 'Logging in', {
                                mso_info['username_field']: username,
                                mso_info['password_field']: password,
                            }, validate_url=True)
                        saml_login_page, urlh = saml_login_page_res
                        if 'Please try again.' in saml_login_page:
                            raise ExtractorError(
                                'We\'re sorry, but either the User ID or Password entered is not correct.')
                    else:
                        # ABC from non-Verizon IP
                        saml_redirect_url = self._html_search_regex(
                            r'var\surl\s*=\s*(["\'])(?P<url>.+?)\1',
                            provider_redirect_page,
                            'SAML Redirect URL', group='url')
                        saml_redirect_url = saml_redirect_url.replace(r'\/', '/')
                        saml_redirect_url = saml_redirect_url.replace(r'\-', '-')
                        saml_redirect_url = saml_redirect_url.replace(r'\x26', '&')
                        saml_login_page = self._download_webpage(
                            saml_redirect_url, video_id,
                            'Downloading SAML Login Page')
                        saml_login_page, urlh = post_form(
                            [saml_login_page, saml_redirect_url], 'Logging in', {
                                mso_info['username_field']: username,
                                mso_info['password_field']: password,
                            }, validate_url=True)
                        if 'Please try again.' in saml_login_page:
                            raise ExtractorError(
                                'Failed to login, incorrect User ID or Password.')
                    saml_login_url = self._search_regex(
                        r'xmlHttp\.open\("POST"\s*,\s*(["\'])(?P<url>.+?)\1',
                        saml_login_page, 'SAML Login URL', group='url')
                    saml_response_json = self._download_json(
                        saml_login_url, video_id, 'Downloading SAML Response',
                        headers={'Content-Type': 'text/xml'})
                    self._download_webpage(
                        saml_response_json['targetValue'], video_id,
                        'Confirming Login', data=urlencode_postdata({
                            'SAMLResponse': saml_response_json['SAMLResponse'],
                            'RelayState': saml_response_json['RelayState'],
                        }), headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                        })
                elif mso_id in ('Spectrum', 'Charter_Direct'):
                    # Spectrum's login for is dynamically loaded via JS so we need to hardcode the flow
                    # as a one-off implementation.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    provider_login_page_res = post_form(
                        provider_redirect_page_res, self._DOWNLOADING_LOGIN_PAGE)
                    saml_login_page, urlh = provider_login_page_res
                    relay_state = self._search_regex(
                        r'RelayState\s*=\s*"(?P<relay>.+?)";',
                        saml_login_page, 'RelayState', group='relay')
                    saml_request = self._search_regex(
                        r'SAMLRequest\s*=\s*"(?P<saml_request>.+?)";',
                        saml_login_page, 'SAMLRequest', group='saml_request')
                    login_json = {
                        mso_info['username_field']: username,
                        mso_info['password_field']: password,
                        'RelayState': relay_state,
                        'SAMLRequest': saml_request,
                    }
                    saml_response_json = self._download_json(
                        'https://tveauthn.spectrum.net/tveauthentication/api/v1/manualAuth', video_id,
                        'Downloading SAML Response',
                        data=json.dumps(login_json).encode(),
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                        })
                    self._download_webpage(
                        saml_response_json['SAMLRedirectUri'], video_id,
                        'Confirming Login', data=urlencode_postdata({
                            'SAMLResponse': saml_response_json['SAMLResponse'],
                            'RelayState': relay_state,
                        }), headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                        })
                elif mso_id == 'slingtv':
                    # SlingTV has a meta-refresh based authentication, but also
                    # looks at the tab history to count the number of times the
                    # browser has been on a page

                    first_bookend_page, urlh = provider_redirect_page_res

                    hidden_data = self._hidden_inputs(first_bookend_page)
                    hidden_data['history'] = 1

                    provider_login_page_res = self._download_webpage_handle(
                        urlh.url, video_id, 'Sending first bookend',
                        query=hidden_data)

                    provider_association_redirect, urlh = post_form(
                        provider_login_page_res, 'Logging in', {
                            mso_info['username_field']: username,
                            mso_info['password_field']: password,
                        }, validate_url=True)

                    provider_refresh_redirect_url = extract_redirect_url(
                        provider_association_redirect, url=urlh.url)

                    last_bookend_page, urlh = self._download_webpage_handle(
                        provider_refresh_redirect_url, video_id,
                        'Downloading Auth Association Redirect Page')
                    hidden_data = self._hidden_inputs(last_bookend_page)
                    hidden_data['history'] = 3

                    mvpd_confirm_page_res = self._download_webpage_handle(
                        urlh.url, video_id, 'Sending final bookend',
                        query=hidden_data)

                    post_form(mvpd_confirm_page_res, 'Confirming Login')
                elif mso_id == 'Suddenlink':
                    # Suddenlink is similar to SlingTV in using a tab history count and a meta refresh,
                    # but they also do a dynmaic redirect using javascript that has to be followed as well
                    first_bookend_page, urlh = post_form(
                        provider_redirect_page_res, 'Pressing Continue...')

                    hidden_data = self._hidden_inputs(first_bookend_page)
                    hidden_data['history_val'] = 1

                    provider_login_redirect_page_res = self._download_webpage_handle(
                        urlh.url, video_id, 'Sending First Bookend',
                        query=hidden_data)

                    provider_login_redirect_page, urlh = provider_login_redirect_page_res

                    # Some website partners seem to not have the extra ajaxurl redirect step, so we check if we already
                    # have the login prompt or not
                    if 'id="password" type="password" name="password"' in provider_login_redirect_page:
                        provider_login_page_res = provider_login_redirect_page_res
                    else:
                        provider_tryauth_url = self._html_search_regex(
                            r'url:\s*[\'"]([^\'"]+)', provider_login_redirect_page, 'ajaxurl')
                        provider_tryauth_page = self._download_webpage(
                            provider_tryauth_url, video_id, 'Submitting TryAuth',
                            query=hidden_data)

                        provider_login_page_res = self._download_webpage_handle(
                            f'https://authorize.suddenlink.net/saml/module.php/authSynacor/login.php?AuthState={provider_tryauth_page}',
                            video_id, 'Getting Login Page',
                            query=hidden_data)

                    provider_association_redirect, urlh = post_form(
                        provider_login_page_res, 'Logging in', {
                            mso_info['username_field']: username,
                            mso_info['password_field']: password,
                        }, validate_url=True)

                    provider_refresh_redirect_url = extract_redirect_url(
                        provider_association_redirect, url=urlh.url)

                    last_bookend_page, urlh = self._download_webpage_handle(
                        provider_refresh_redirect_url, video_id,
                        'Downloading Auth Association Redirect Page')

                    hidden_data = self._hidden_inputs(last_bookend_page)
                    hidden_data['history_val'] = 3

                    mvpd_confirm_page_res = self._download_webpage_handle(
                        urlh.url, video_id, 'Sending Final Bookend',
                        query=hidden_data)

                    post_form(mvpd_confirm_page_res, 'Confirming Login')
                elif mso_id == 'Fubo':
                    _, urlh = provider_redirect_page_res

                    fubo_response = self._download_json(
                        'https://api.fubo.tv/partners/tve/connect', video_id,
                        'Authenticating with Fubo', 'Unable to authenticate with Fubo',
                        query=parse_qs(urlh.url), data=json.dumps({
                            'username': username,
                            'password': password,
                        }).encode(), headers={
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        })

                    self._request_webpage(
                        'https://sp.auth.adobe.com/adobe-services/oauth2', video_id,
                        'Authenticating with Adobe', 'Failed to authenticate with Adobe',
                        query={
                            'code': fubo_response['code'],
                            'state': fubo_response['state'],
                        })
                else:
                    # Some providers (e.g. DIRECTV NOW) have another meta refresh
                    # based redirect that should be followed.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    provider_refresh_redirect_url = extract_redirect_url(
                        provider_redirect_page, url=urlh.url)
                    if provider_refresh_redirect_url:
                        provider_redirect_page_res = self._download_webpage_handle(
                            provider_refresh_redirect_url, video_id,
                            'Downloading Provider Redirect Page (meta refresh)')
                    provider_login_page_res = post_form(
                        provider_redirect_page_res, self._DOWNLOADING_LOGIN_PAGE)
                    form_data = {
                        mso_info.get('username_field', 'username'): username,
                        mso_info.get('password_field', 'password'): password,
                    }
                    if mso_id in ('Cablevision', 'AlticeOne'):
                        form_data['_eventId_proceed'] = ''
                    mvpd_confirm_page_res = post_form(
                        provider_login_page_res, 'Logging in', form_data, validate_url=True)
                    if mso_id != 'Rogers':
                        post_form(mvpd_confirm_page_res, 'Confirming Login')

                try:
                    session = self._download_webpage(
                        self._SERVICE_PROVIDER_TEMPLATE % 'session', video_id,
                        'Retrieving Session', data=urlencode_postdata({
                            '_method': 'GET',
                            'requestor_id': requestor_id,
                            'reg_code': reg_code,
                        }), headers=mvpd_headers)
                except ExtractorError as e:
                    if not mso_id and isinstance(e.cause, HTTPError) and e.cause.status == 401:
                        raise_mvpd_required()
                    raise
                if '<pendingLogout' in session:
                    self.cache.store(self._MVPD_CACHE, requestor_id, {})
                    continue
                authn_token = unescapeHTML(xml_text(session, 'authnToken'))
                requestor_info['authn_token'] = authn_token
                self.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

            authz_token = requestor_info.get(guid)
            if authz_token and is_expired(authz_token, 'simpleTokenTTL'):
                authz_token = None
            if not authz_token:
                authorize = self._download_webpage(
                    self._SERVICE_PROVIDER_TEMPLATE % 'authorize', video_id,
                    'Retrieving Authorization Token', data=urlencode_postdata({
                        'resource_id': resource,
                        'requestor_id': requestor_id,
                        'authentication_token': authn_token,
                        'mso_id': xml_text(authn_token, 'simpleTokenMsoID'),
                        'userMeta': '1',
                    }), headers=mvpd_headers)
                if '<pendingLogout' in authorize:
                    self.cache.store(self._MVPD_CACHE, requestor_id, {})
                    continue
                if '<error' in authorize:
                    raise ExtractorError(xml_text(authorize, 'details'), expected=True)
                authz_token = unescapeHTML(xml_text(authorize, 'authzToken'))
                requestor_info[guid] = authz_token
                self.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

            mvpd_headers.update({
                'ap_19': xml_text(authn_token, 'simpleSamlNameID'),
                'ap_23': xml_text(authn_token, 'simpleSamlSessionIndex'),
            })

            short_authorize = self._download_webpage(
                self._SERVICE_PROVIDER_TEMPLATE % 'shortAuthorize',
                video_id, 'Retrieving Media Token', data=urlencode_postdata({
                    'authz_token': authz_token,
                    'requestor_id': requestor_id,
                    'session_guid': xml_text(authn_token, 'simpleTokenAuthenticationGuid'),
                    'hashed_guid': 'false',
                }), headers=mvpd_headers)
            if '<pendingLogout' in short_authorize:
                self.cache.store(self._MVPD_CACHE, requestor_id, {})
                continue
            return short_authorize