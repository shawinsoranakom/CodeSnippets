def _extract_response(self, item_id, query, note='Downloading API JSON', headers=None,
                          ytcfg=None, check_get_keys=None, ep='browse', fatal=True, api_hostname=None,
                          default_client='web'):
        raise_for_incomplete = bool(self._configuration_arg('raise_incomplete_data', ie_key=CONFIGURATION_ARG_KEY))
        # Incomplete Data should be a warning by default when retries are exhausted, while other errors should be fatal.
        icd_retries = iter(self.RetryManager(fatal=raise_for_incomplete))
        icd_rm = next(icd_retries)
        main_retries = iter(self.RetryManager())
        main_rm = next(main_retries)
        # Manual retry loop for multiple RetryManagers
        # The proper RetryManager MUST be advanced after an error
        # and its result MUST be checked if the manager is non fatal
        while True:
            try:
                response = self._call_api(
                    ep=ep, fatal=True, headers=headers,
                    video_id=item_id, query=query, note=note,
                    context=self._extract_context(ytcfg, default_client),
                    api_hostname=api_hostname, default_client=default_client)
            except ExtractorError as e:
                if not isinstance(e.cause, network_exceptions):
                    return self._error_or_warning(e, fatal=fatal)
                elif not isinstance(e.cause, HTTPError):
                    main_rm.error = e
                    next(main_retries)
                    continue

                first_bytes = e.cause.response.read(512)
                if not is_html(first_bytes):
                    yt_error = try_get(
                        self._parse_json(
                            self._webpage_read_content(e.cause.response, None, item_id, prefix=first_bytes) or '{}', item_id, fatal=False),
                        lambda x: x['error']['message'], str)
                    if yt_error:
                        self._report_alerts([('ERROR', yt_error)], fatal=False)
                # Downloading page may result in intermittent 5xx HTTP error
                # Sometimes a 404 is also received. See: https://github.com/ytdl-org/youtube-dl/issues/28289
                # We also want to catch all other network exceptions since errors in later pages can be troublesome
                # See https://github.com/yt-dlp/yt-dlp/issues/507#issuecomment-880188210
                if e.cause.status not in (403, 429):
                    main_rm.error = e
                    next(main_retries)
                    continue
                return self._error_or_warning(e, fatal=fatal)

            try:
                self._extract_and_report_alerts(response, only_once=True)
            except ExtractorError as e:
                # YouTube's servers may return errors we want to retry on in a 200 OK response
                # See: https://github.com/yt-dlp/yt-dlp/issues/839
                if 'unknown error' in e.msg.lower():
                    main_rm.error = e
                    next(main_retries)
                    continue
                return self._error_or_warning(e, fatal=fatal)
            # Youtube sometimes sends incomplete data
            # See: https://github.com/ytdl-org/youtube-dl/issues/28194
            if not traverse_obj(response, *variadic(check_get_keys)):
                icd_rm.error = ExtractorError('Incomplete data received', expected=True)
                should_retry = next(icd_retries, None)
                if not should_retry:
                    return None
                continue

            return response