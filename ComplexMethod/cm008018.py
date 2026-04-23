def _calc_headers(self, info_dict, load_cookies=False):
        res = HTTPHeaderDict(self.params['http_headers'], info_dict.get('http_headers'))
        clean_headers(res)

        if load_cookies:  # For --load-info-json
            self._load_cookies(res.get('Cookie'), autoscope=info_dict['url'])  # compat
            self._load_cookies(info_dict.get('cookies'), autoscope=False)
        # The `Cookie` header is removed to prevent leaks and unscoped cookies.
        # See: https://github.com/yt-dlp/yt-dlp/security/advisories/GHSA-v8mc-9377-rwjj
        res.pop('Cookie', None)
        cookies = self.cookiejar.get_cookies_for_url(info_dict['url'])
        if cookies:
            encoder = LenientSimpleCookie()
            values = []
            for cookie in cookies:
                _, value = encoder.value_encode(cookie.value)
                values.append(f'{cookie.name}={value}')
                if cookie.domain:
                    values.append(f'Domain={cookie.domain}')
                if cookie.path:
                    values.append(f'Path={cookie.path}')
                if cookie.secure:
                    values.append('Secure')
                if cookie.expires:
                    values.append(f'Expires={cookie.expires}')
                if cookie.version:
                    values.append(f'Version={cookie.version}')
            info_dict['cookies'] = '; '.join(values)

        if 'X-Forwarded-For' not in res:
            x_forwarded_for_ip = info_dict.get('__x_forwarded_for_ip')
            if x_forwarded_for_ip:
                res['X-Forwarded-For'] = x_forwarded_for_ip

        return res