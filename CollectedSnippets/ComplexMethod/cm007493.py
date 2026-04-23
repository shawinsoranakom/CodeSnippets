def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            return

        try:
            glb_id = (self._download_json(
                'https://login.globo.com/api/authentication', None, data=json.dumps({
                    'payload': {
                        'email': email,
                        'password': password,
                        'serviceId': 4654,
                    },
                }).encode(), headers={
                    'Content-Type': 'application/json; charset=utf-8',
                }) or {}).get('glbId')
            if glb_id:
                self._set_cookie('.globo.com', 'GLBID', glb_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                resp = self._parse_json(e.cause.read(), None)
                raise ExtractorError(resp.get('userMessage') or resp['id'], expected=True)
            raise