def _extract_mvpd_auth(self, url, video_id, requestor_id, resource):
        def xml_text(xml_str, tag):
            return self._search_regex(
                '<%s>(.+?)</%s>' % (tag, tag), xml_str, tag)

        def is_expired(token, date_ele):
            token_expires = unified_timestamp(re.sub(r'[_ ]GMT', '', xml_text(token, date_ele)))
            return token_expires and token_expires <= int(time.time())

        def post_form(form_page_res, note, data={}):
            form_page, urlh = form_page_res
            post_url = self._html_search_regex(r'<form[^>]+action=(["\'])(?P<url>.+?)\1', form_page, 'post url', group='url')
            if not re.match(r'https?://', post_url):
                post_url = compat_urlparse.urljoin(urlh.geturl(), post_url)
            form_data = self._hidden_inputs(form_page)
            form_data.update(data)
            return self._download_webpage_handle(
                post_url, video_id, note, data=urlencode_postdata(form_data), headers={
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
                r'(?:[a-z-]+="[^"]+"\s+)*?content="%s' % REDIRECT_REGEX,
                html, 'meta refresh redirect',
                default=NO_DEFAULT if fatal else None, fatal=fatal)
            if not redirect_url:
                return None
            if url:
                redirect_url = compat_urlparse.urljoin(url, unescapeHTML(redirect_url))
            return redirect_url

        mvpd_headers = {
            'ap_42': 'anonymous',
            'ap_11': 'Linux i686',
            'ap_z': self._USER_AGENT,
            'User-Agent': self._USER_AGENT,
        }

        guid = xml_text(resource, 'guid') if '<' in resource else resource
        count = 0
        while count < 2:
            requestor_info = self._downloader.cache.load(self._MVPD_CACHE, requestor_id) or {}
            authn_token = requestor_info.get('authn_token')
            if authn_token and is_expired(authn_token, 'simpleTokenExpires'):
                authn_token = None
            if not authn_token:
                # TODO add support for other TV Providers
                mso_id = self._downloader.params.get('ap_mso')
                if not mso_id:
                    raise_mvpd_required()
                username, password = self._get_login_info('ap_username', 'ap_password', mso_id)
                if not username or not password:
                    raise_mvpd_required()
                mso_info = MSO_INFO[mso_id]

                provider_redirect_page_res = self._download_webpage_handle(
                    self._SERVICE_PROVIDER_TEMPLATE % 'authenticate/saml', video_id,
                    'Downloading Provider Redirect Page', query={
                        'noflash': 'true',
                        'mso_id': mso_id,
                        'requestor_id': requestor_id,
                        'no_iframe': 'false',
                        'domain_name': 'adobe.com',
                        'redirect_url': url,
                    })

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
                    else:
                        if '<form name="signin"' in provider_redirect_page:
                            provider_login_page_res = provider_redirect_page_res
                        elif 'http-equiv="refresh"' in provider_redirect_page:
                            oauth_redirect_url = extract_redirect_url(
                                provider_redirect_page, fatal=True)
                            provider_login_page_res = self._download_webpage_handle(
                                oauth_redirect_url, video_id,
                                self._DOWNLOADING_LOGIN_PAGE)
                        else:
                            provider_login_page_res = post_form(
                                provider_redirect_page_res,
                                self._DOWNLOADING_LOGIN_PAGE)

                        mvpd_confirm_page_res = post_form(
                            provider_login_page_res, 'Logging in', {
                                mso_info['username_field']: username,
                                mso_info['password_field']: password,
                            })
                        mvpd_confirm_page, urlh = mvpd_confirm_page_res
                        if '<button class="submit" value="Resume">Resume</button>' in mvpd_confirm_page:
                            post_form(mvpd_confirm_page_res, 'Confirming Login')
                elif mso_id == 'Verizon':
                    # In general, if you're connecting from a Verizon-assigned IP,
                    # you will not actually pass your credentials.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    if 'Please wait ...' in provider_redirect_page:
                        saml_redirect_url = self._html_search_regex(
                            r'self\.parent\.location=(["\'])(?P<url>.+?)\1',
                            provider_redirect_page,
                            'SAML Redirect URL', group='url')
                        saml_login_page = self._download_webpage(
                            saml_redirect_url, video_id,
                            'Downloading SAML Login Page')
                    else:
                        saml_login_page_res = post_form(
                            provider_redirect_page_res, 'Logging in', {
                                mso_info['username_field']: username,
                                mso_info['password_field']: password,
                            })
                        saml_login_page, urlh = saml_login_page_res
                        if 'Please try again.' in saml_login_page:
                            raise ExtractorError(
                                'We\'re sorry, but either the User ID or Password entered is not correct.')
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
                            'RelayState': saml_response_json['RelayState']
                        }), headers={
                            'Content-Type': 'application/x-www-form-urlencoded'
                        })
                else:
                    # Some providers (e.g. DIRECTV NOW) have another meta refresh
                    # based redirect that should be followed.
                    provider_redirect_page, urlh = provider_redirect_page_res
                    provider_refresh_redirect_url = extract_redirect_url(
                        provider_redirect_page, url=urlh.geturl())
                    if provider_refresh_redirect_url:
                        provider_redirect_page_res = self._download_webpage_handle(
                            provider_refresh_redirect_url, video_id,
                            'Downloading Provider Redirect Page (meta refresh)')
                    provider_login_page_res = post_form(
                        provider_redirect_page_res, self._DOWNLOADING_LOGIN_PAGE)
                    mvpd_confirm_page_res = post_form(provider_login_page_res, 'Logging in', {
                        mso_info.get('username_field', 'username'): username,
                        mso_info.get('password_field', 'password'): password,
                    })
                    if mso_id != 'Rogers':
                        post_form(mvpd_confirm_page_res, 'Confirming Login')

                session = self._download_webpage(
                    self._SERVICE_PROVIDER_TEMPLATE % 'session', video_id,
                    'Retrieving Session', data=urlencode_postdata({
                        '_method': 'GET',
                        'requestor_id': requestor_id,
                    }), headers=mvpd_headers)
                if '<pendingLogout' in session:
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                authn_token = unescapeHTML(xml_text(session, 'authnToken'))
                requestor_info['authn_token'] = authn_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

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
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                if '<error' in authorize:
                    raise ExtractorError(xml_text(authorize, 'details'), expected=True)
                authz_token = unescapeHTML(xml_text(authorize, 'authzToken'))
                requestor_info[guid] = authz_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

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
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                count += 1
                continue
            return short_authorize