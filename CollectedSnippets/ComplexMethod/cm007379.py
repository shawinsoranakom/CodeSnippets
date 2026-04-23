def _login(self):
        useremail, password = self._get_login_info()
        if useremail is None:
            return

        login_page_req = sanitized_Request(self._LOGIN_URL)
        self._set_cookie('facebook.com', 'locale', 'en_US')
        login_page = self._download_webpage(login_page_req, None,
                                            note='Downloading login page',
                                            errnote='Unable to download login page')
        lsd = self._search_regex(
            r'<input type="hidden" name="lsd" value="([^"]*)"',
            login_page, 'lsd')
        lgnrnd = self._search_regex(r'name="lgnrnd" value="([^"]*?)"', login_page, 'lgnrnd')

        login_form = {
            'email': useremail,
            'pass': password,
            'lsd': lsd,
            'lgnrnd': lgnrnd,
            'next': 'http://facebook.com/home.php',
            'default_persistent': '0',
            'legacy_return': '1',
            'timezone': '-60',
            'trynum': '1',
        }
        request = sanitized_Request(self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            login_results = self._download_webpage(request, None,
                                                   note='Logging in', errnote='unable to fetch login page')
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                error = self._html_search_regex(
                    r'(?s)<div[^>]+class=(["\']).*?login_error_box.*?\1[^>]*><div[^>]*>.*?</div><div[^>]*>(?P<error>.+?)</div>',
                    login_results, 'login error', default=None, group='error')
                if error:
                    raise ExtractorError('Unable to login: %s' % error, expected=True)
                self._downloader.report_warning('unable to log in: bad username/password, or exceeded login rate limit (~3/min). Check credentials or wait.')
                return

            fb_dtsg = self._search_regex(
                r'name="fb_dtsg" value="(.+?)"', login_results, 'fb_dtsg', default=None)
            h = self._search_regex(
                r'name="h"\s+(?:\w+="[^"]+"\s+)*?value="([^"]+)"', login_results, 'h', default=None)

            if not fb_dtsg or not h:
                return

            check_form = {
                'fb_dtsg': fb_dtsg,
                'h': h,
                'name_action_selected': 'dont_save',
            }
            check_req = sanitized_Request(self._CHECKPOINT_URL, urlencode_postdata(check_form))
            check_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            check_response = self._download_webpage(check_req, None,
                                                    note='Confirming login')
            if re.search(r'id="checkpointSubmitButton"', check_response) is not None:
                self._downloader.report_warning('Unable to confirm login, you have to login in your browser and authorize the login.')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning('unable to log in: %s' % error_to_compat_str(err))
            return