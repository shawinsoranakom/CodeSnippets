def _call_api(self, version, path, video_id):
        try:
            return self._download_json(
                f'https://apiv2.sonyliv.com/AGL/{version}/A/ENG/WEB/{path}',
                video_id, headers=self._HEADERS)['resultObj']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 406 and self._parse_json(
                    e.cause.response.read().decode(), video_id)['message'] == 'Please subscribe to watch this content':
                self.raise_login_required(self._LOGIN_HINT, method=None)
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                message = self._parse_json(
                    e.cause.response.read().decode(), video_id)['message']
                if message == 'Geoblocked Country':
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                raise ExtractorError(message)
            raise