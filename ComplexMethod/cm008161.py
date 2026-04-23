def _call_api(self, ep, item_id, query=None, headers=None, fatal=True, note=None):
        if headers is None:
            headers = {}
        if 'User-Agent' not in headers and self.patreon_user_agent:
            headers['User-Agent'] = self.patreon_user_agent
        if query:
            query.update({'json-api-version': 1.0})

        try:
            return self._download_json(
                f'https://www.patreon.com/api/{ep}',
                item_id, note=note if note else 'Downloading API JSON',
                query=query, fatal=fatal, headers=headers,
                # If not using Patreon mobile UA, we need impersonation due to Cloudflare
                impersonate=not self.patreon_user_agent)
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError) or mimetype2ext(e.cause.response.headers.get('Content-Type')) != 'json':
                raise
            err_json = self._parse_json(self._webpage_read_content(e.cause.response, None, item_id), item_id, fatal=False)
            err_message = traverse_obj(err_json, ('errors', ..., 'detail'), get_all=False)
            if err_message:
                raise ExtractorError(f'Patreon said: {err_message}', expected=True)
            raise