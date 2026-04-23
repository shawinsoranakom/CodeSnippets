def proxy_open(self, req, proxy, type):
        orig_type = req.type
        proxy_type, user, password, hostport = _parse_proxy(proxy)
        if proxy_type is None:
            proxy_type = orig_type

        if req.host and proxy_bypass(req.host):
            return None

        if user and password:
            user_pass = '%s:%s' % (unquote(user),
                                   unquote(password))
            creds = base64.b64encode(user_pass.encode()).decode("ascii")
            req.add_header('Proxy-authorization', 'Basic ' + creds)
        hostport = unquote(hostport)
        req.set_proxy(hostport, proxy_type)
        if orig_type == proxy_type or orig_type == 'https':
            # let other handlers take care of it
            return None
        else:
            # need to start over, because the other handlers don't
            # grok the proxy's URL type
            # e.g. if we have a constructor arg proxies like so:
            # {'http': 'ftp://proxy.example.com'}, we may end up turning
            # a request for http://acme.example.com/a into one for
            # ftp://proxy.example.com/a
            return self.parent.open(req, timeout=req.timeout)