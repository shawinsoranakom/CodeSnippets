def _extract_webpage(self, url, item_id, fatal=True):
        webpage, data = None, None
        for retry in self.RetryManager(fatal=fatal):
            try:
                webpage = self._download_webpage(url, item_id, note='Downloading webpage')
                data = self.extract_yt_initial_data(item_id, webpage or '', fatal=fatal) or {}
            except ExtractorError as e:
                if isinstance(e.cause, network_exceptions):
                    if not isinstance(e.cause, HTTPError) or e.cause.status not in (403, 429):
                        retry.error = e
                        continue
                self._error_or_warning(e, fatal=fatal)
                break

            try:
                self._extract_and_report_alerts(data)
            except ExtractorError as e:
                self._error_or_warning(e, fatal=fatal)
                break

            # Sometimes youtube returns a webpage with incomplete ytInitialData
            # See: https://github.com/yt-dlp/yt-dlp/issues/116
            if not traverse_obj(data, 'contents', 'currentVideoEndpoint', 'onResponseReceivedActions'):
                retry.error = ExtractorError('Incomplete yt initial data received')
                data = None
                continue

        return webpage, data