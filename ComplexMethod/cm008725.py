def _generate_cookie_auth_headers(self, *, ytcfg=None, delegated_session_id=None, user_session_id=None, session_index=None, origin=None, **kwargs):
        headers = {}
        delegated_session_id = delegated_session_id or self._extract_delegated_session_id(ytcfg)
        if delegated_session_id:
            headers['X-Goog-PageId'] = delegated_session_id
        if session_index is None:
            session_index = self._extract_session_index(ytcfg)
        if delegated_session_id or session_index is not None:
            headers['X-Goog-AuthUser'] = session_index if session_index is not None else 0

        auth = self._get_sid_authorization_header(origin, user_session_id=user_session_id or self._extract_user_session_id(ytcfg))
        if auth is not None:
            headers['Authorization'] = auth
            headers['X-Origin'] = origin

        if traverse_obj(ytcfg, 'LOGGED_IN', expected_type=bool):
            headers['X-Youtube-Bootstrap-Logged-In'] = 'true'

        return headers