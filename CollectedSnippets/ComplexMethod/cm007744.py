def _call_api(self, path, video_id, data=None):
        headers = {
            'X-Api-Key': self._API_KEY,
        }
        if self._access_token:
            headers['Authorization'] = 'Bearer ' + self._access_token
        try:
            return self._download_json(
                'https://api2.fox.com/v2.0/' + path,
                video_id, data=data, headers=headers)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                entitlement_issues = self._parse_json(
                    e.cause.read().decode(), video_id)['entitlementIssues']
                for e in entitlement_issues:
                    if e.get('errorCode') == 1005:
                        raise ExtractorError(
                            'This video is only available via cable service provider '
                            'subscription. You may want to use --cookies.', expected=True)
                messages = ', '.join([e['message'] for e in entitlement_issues])
                raise ExtractorError(messages, expected=True)
            raise