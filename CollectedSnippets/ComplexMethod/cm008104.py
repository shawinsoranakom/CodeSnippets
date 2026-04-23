def _call_api(self, *args, **kwargs):
        non_fatal = kwargs.get('fatal') is False
        if non_fatal:
            del kwargs['fatal']
        query = kwargs.get('query', {}).copy()
        for is_first_attempt in (True, False):
            query['client_id'] = self._CLIENT_ID
            kwargs['query'] = query
            try:
                return self._download_json(*args, **kwargs)
            except ExtractorError as e:
                if is_first_attempt and isinstance(e.cause, HTTPError) and e.cause.status in (401, 403):
                    self._store_client_id(None)
                    self._update_client_id()
                    continue
                elif non_fatal:
                    self.report_warning(str(e))
                    return False
                raise