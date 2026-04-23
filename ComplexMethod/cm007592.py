def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}, expected_status=None):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            if 'X-Forwarded-For' not in headers:
                headers['X-Forwarded-For'] = self._x_forwarded_for_ip

        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
            if data is not None or headers:
                url_or_request = sanitized_Request(url_or_request, data, headers)
        exceptions = [compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error]
        if hasattr(ssl, 'CertificateError'):
            exceptions.append(ssl.CertificateError)
        try:
            return self._downloader.urlopen(url_or_request)
        except tuple(exceptions) as err:
            if isinstance(err, compat_urllib_error.HTTPError):
                if self.__can_accept_status_code(err, expected_status):
                    # Retain reference to error to prevent file object from
                    # being closed before it can be read. Works around the
                    # effects of <https://bugs.python.org/issue15002>
                    # introduced in Python 3.4.1.
                    err.fp._error = err
                    return err.fp

            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self.report_warning(errmsg)
                return False