def _calc_headers(self, info_dict, load_cookies=False):
        if load_cookies:  # For --load-info-json
            # load cookies from http_headers in legacy info.json
            self._load_cookies(traverse_obj(info_dict, ('http_headers', 'Cookie'), casesense=False),
                               autoscope=info_dict['url'])
            # load scoped cookies from info.json
            self._load_cookies(info_dict.get('cookies'), autoscope=False)

        cookies = self.cookiejar.get_cookies_for_url(info_dict['url'])
        if cookies:
            # Make a string like name1=val1; attr1=a_val1; ...name2=val2; ...
            # By convention a cookie name can't be a well-known attribute name
            # so this syntax is unambiguous and can be parsed by (eg) SimpleCookie
            encoder = compat_http_cookies_SimpleCookie()
            values = []
            attributes = (('Domain', '='), ('Path', '='), ('Secure',), ('Expires', '='), ('Version', '='))
            attributes = tuple([x[0].lower()] + list(x) for x in attributes)
            for cookie in cookies:
                _, value = encoder.value_encode(cookie.value)
                # Py 2 '' --> '', Py 3 '' --> '""'
                if value == '':
                    value = '""'
                values.append('='.join((cookie.name, value)))
                for attr in attributes:
                    value = getattr(cookie, attr[0], None)
                    if value:
                        values.append('%s%s' % (''.join(attr[1:]), value if len(attr) == 3 else ''))
            info_dict['cookies'] = '; '.join(values)

        res = std_headers.copy()
        res.update(info_dict.get('http_headers') or {})
        res = self._remove_cookie_header(res)

        if 'X-Forwarded-For' not in res:
            x_forwarded_for_ip = info_dict.get('__x_forwarded_for_ip')
            if x_forwarded_for_ip:
                res['X-Forwarded-For'] = x_forwarded_for_ip

        return res or None