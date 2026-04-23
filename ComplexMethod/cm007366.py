def _setup_opener(self):
        timeout_val = self.params.get('socket_timeout')
        self._socket_timeout = 600 if timeout_val is None else float(timeout_val)

        opts_cookiefile = self.params.get('cookiefile')
        opts_proxy = self.params.get('proxy')

        if opts_cookiefile is None:
            self.cookiejar = YoutubeDLCookieJar()
        else:
            opts_cookiefile = expand_path(opts_cookiefile)
            self.cookiejar = YoutubeDLCookieJar(opts_cookiefile)
            if os.access(opts_cookiefile, os.R_OK):
                self.cookiejar.load(ignore_discard=True, ignore_expires=True)

        cookie_processor = YoutubeDLCookieProcessor(self.cookiejar)
        if opts_proxy is not None:
            if opts_proxy == '':
                proxies = {}
            else:
                proxies = {'http': opts_proxy, 'https': opts_proxy}
        else:
            proxies = compat_urllib_request.getproxies()
            # Set HTTPS proxy to HTTP one if given (https://github.com/ytdl-org/youtube-dl/issues/805)
            if 'http' in proxies and 'https' not in proxies:
                proxies['https'] = proxies['http']
        proxy_handler = PerRequestProxyHandler(proxies)

        debuglevel = 1 if self.params.get('debug_printtraffic') else 0
        https_handler = make_HTTPS_handler(self.params, debuglevel=debuglevel)
        ydlh = YoutubeDLHandler(self.params, debuglevel=debuglevel)
        redirect_handler = YoutubeDLRedirectHandler()
        data_handler = compat_urllib_request_DataHandler()

        # When passing our own FileHandler instance, build_opener won't add the
        # default FileHandler and allows us to disable the file protocol, which
        # can be used for malicious purposes (see
        # https://github.com/ytdl-org/youtube-dl/issues/8227)
        file_handler = compat_urllib_request.FileHandler()

        def file_open(*args, **kwargs):
            raise compat_urllib_error.URLError('file:// scheme is explicitly disabled in youtube-dl for security reasons')
        file_handler.file_open = file_open

        opener = compat_urllib_request.build_opener(
            proxy_handler, https_handler, cookie_processor, ydlh, redirect_handler, data_handler, file_handler)

        # Delete the default user-agent header, which would otherwise apply in
        # cases where our custom HTTP handler doesn't come into play
        # (See https://github.com/ytdl-org/youtube-dl/issues/1309 for details)
        opener.addheaders = []
        self._opener = opener