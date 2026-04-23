def _call_api(self, path, video_id, note, data=None):
        # https://tools.ietf.org/html/rfc5849#section-3
        base_url = self._API_DOMAIN + '/core/' + path
        query = [
            ('oauth_consumer_key', self._API_PARAMS['oAuthKey']),
            ('oauth_nonce', ''.join([random.choice(string.ascii_letters) for _ in range(32)])),
            ('oauth_signature_method', 'HMAC-SHA1'),
            ('oauth_timestamp', int(time.time())),
        ]
        if self._TOKEN:
            query.append(('oauth_token', self._TOKEN))
        encoded_query = compat_urllib_parse_urlencode(query)
        headers = self.geo_verification_headers()
        if data:
            data = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        base_string = '&'.join([
            'POST' if data else 'GET',
            compat_urllib_parse.quote(base_url, ''),
            compat_urllib_parse.quote(encoded_query, '')])
        oauth_signature = base64.b64encode(hmac.new(
            (self._API_PARAMS['oAuthSecret'] + '&' + self._TOKEN_SECRET).encode('ascii'),
            base_string.encode(), hashlib.sha1).digest()).decode()
        encoded_query += '&oauth_signature=' + compat_urllib_parse.quote(oauth_signature, '')
        try:
            return self._download_json(
                '?'.join([base_url, encoded_query]), video_id,
                note='Downloading %s JSON metadata' % note, headers=headers, data=data)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                raise ExtractorError(json.loads(e.cause.read().decode())['message'], expected=True)
            raise