def _call_api(self, path, video_id=None, app_code=None, query=None):
        if not query:
            query = {}
        query.update({
            'client_key': '773aea60-0e80-41bb-9c7f-e6d7c3ad17fb',
            'output': 'json',
        })
        if video_id:
            query.update({
                'appCode': app_code,
                'idMedia': video_id,
            })
        if self._access_token:
            query['access_token'] = self._access_token
        try:
            return self._download_json(
                'https://services.radio-canada.ca/media/' + path, video_id, query=query)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (401, 422):
                data = self._parse_json(e.cause.response.read().decode(), None)
                error = data.get('error_description') or data['errorMessage']['text']
                raise ExtractorError(error, expected=True)
            raise