def _extract_status(self, twid):
        if self._selected_api not in ('graphql', 'legacy', 'syndication'):
            raise ExtractorError(f'{self._selected_api!r} is not a valid API selection', expected=True)

        try:
            if self.is_logged_in or self._selected_api == 'graphql':
                status = self._graphql_to_legacy(self._call_graphql_api(self._GRAPHQL_ENDPOINT, twid), twid)
            elif self._selected_api == 'legacy':
                status = self._call_api(f'statuses/show/{twid}.json', twid, {
                    'cards_platform': 'Web-12',
                    'include_cards': 1,
                    'include_reply_count': 1,
                    'include_user_entities': 0,
                    'tweet_mode': 'extended',
                })
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError) or e.cause.status != 429:
                raise
            self.report_warning('Rate-limit exceeded; falling back to syndication endpoint')
            status = self._call_syndication_api(twid)

        if self._selected_api == 'syndication':
            status = self._call_syndication_api(twid)

        return traverse_obj(status, 'retweeted_status', None, expected_type=dict) or {}