def _call_api(self, object_type, xid, object_fields, note, filter_extra=None):
        if not self._HEADERS.get('Authorization'):
            cookies = self._get_dailymotion_cookies()
            token = self._get_cookie_value(cookies, 'access_token') or self._get_cookie_value(cookies, 'client_token')
            if not token:
                data = {
                    'client_id': 'f1a362d288c1b98099c7',
                    'client_secret': 'eea605b96e01c796ff369935357eca920c5da4c5',
                }
                username, password = self._get_login_info()
                if username:
                    data.update({
                        'grant_type': 'password',
                        'password': password,
                        'username': username,
                    })
                else:
                    data['grant_type'] = 'client_credentials'
                try:
                    token = self._download_json(
                        'https://graphql.api.dailymotion.com/oauth/token',
                        None, 'Downloading Access Token',
                        data=urlencode_postdata(data))['access_token']
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                        raise ExtractorError(self._parse_json(
                            e.cause.read().decode(), xid)['error_description'], expected=True)
                    raise
                self._set_dailymotion_cookie('access_token' if username else 'client_token', token)
            self._HEADERS['Authorization'] = 'Bearer ' + token

        resp = self._download_json(
            'https://graphql.api.dailymotion.com/', xid, note, data=json.dumps({
                'query': '''{
  %s(xid: "%s"%s) {
    %s
  }
}''' % (object_type, xid, ', ' + filter_extra if filter_extra else '', object_fields),
            }).encode(), headers=self._HEADERS)
        obj = resp['data'][object_type]
        if not obj:
            raise ExtractorError(resp['errors'][0]['message'], expected=True)
        return obj