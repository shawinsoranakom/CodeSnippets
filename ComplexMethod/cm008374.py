def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None,
                         headers=None, query=None, expected_status=None, impersonate=None, require_impersonation=False):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if not self._downloader._first_webpage_request:
            sleep_interval = self.get_param('sleep_interval_requests') or 0
            if sleep_interval > 0:
                self.to_screen(f'Sleeping {sleep_interval} seconds ...')
                time.sleep(sleep_interval)
        else:
            self._downloader._first_webpage_request = False

        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen(str(note))
            else:
                self.to_screen(f'{video_id}: {note}')

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            headers = (headers or {}).copy()
            headers.setdefault('X-Forwarded-For', self._x_forwarded_for_ip)

        extensions = {}

        available_target, requested_targets = self._downloader._parse_impersonate_targets(impersonate)
        if available_target:
            extensions['impersonate'] = available_target
        elif requested_targets:
            msg = 'The extractor is attempting impersonation'
            if require_impersonation:
                raise ExtractorError(
                    self._downloader._unavailable_targets_message(requested_targets, note=msg, is_error=True),
                    expected=True)
            self.report_warning(
                self._downloader._unavailable_targets_message(requested_targets, note=msg), only_once=True)

        try:
            return self._downloader.urlopen(self._create_request(url_or_request, data, headers, query, extensions))
        except network_exceptions as err:
            if isinstance(err, HTTPError):
                if self.__can_accept_status_code(err, expected_status):
                    return err.response

            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = f'{errnote}: {err}'
            if fatal:
                raise ExtractorError(errmsg, cause=err)
            else:
                self.report_warning(errmsg)
                return False