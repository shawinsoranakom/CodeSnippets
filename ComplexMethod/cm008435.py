def _call_api(self, path, video_id, query={}, graphql=False):
        headers = self._set_base_headers(legacy=not graphql and self._selected_api == 'legacy')
        headers.update({
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en',
            'x-twitter-active-user': 'yes',
        } if self.is_logged_in else {
            'x-guest-token': self._fetch_guest_token(video_id),
        })
        allowed_status = {400, 401, 403, 404} if graphql else {403}
        result = self._download_json(
            (self._GRAPHQL_API_BASE if graphql else self._API_BASE) + path,
            video_id, headers=headers, query=query, expected_status=allowed_status,
            note=f'Downloading {"GraphQL" if graphql else "legacy API"} JSON')

        if error_msg := ', '.join(set(traverse_obj(result, ('errors', ..., 'message', {str})))):
            # Errors with the message 'Dependency: Unspecified' are a false positive
            # See https://github.com/yt-dlp/yt-dlp/issues/15963
            if error_msg.lower() == 'dependency: unspecified':
                self.write_debug(f'Ignoring Twitter API error: "{error_msg}"')
            elif 'not authorized' in error_msg.lower():
                self.raise_login_required(remove_end(error_msg, '.'))
            else:
                raise ExtractorError(f'Error(s) while querying API: {error_msg or "Unknown error"}')

        return result