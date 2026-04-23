def do_proxy_auth(self, username, password):
        if username is None and password is None:
            return True

        proxy_auth_header = self.headers.get('Proxy-Authorization', None)
        if proxy_auth_header is None:
            return self.proxy_auth_error()

        if not proxy_auth_header.startswith('Basic '):
            return self.proxy_auth_error()

        auth = proxy_auth_header[6:]

        try:
            auth_username, auth_password = base64.b64decode(auth).decode().split(':', 1)
        except Exception:
            return self.proxy_auth_error()

        if auth_username != (username or '') or auth_password != (password or ''):
            return self.proxy_auth_error()
        return True