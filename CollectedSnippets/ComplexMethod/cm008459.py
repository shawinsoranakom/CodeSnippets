def _call_api(self, ep, video_id, query=None, data=None, headers=None, fatal=True,
                  note='Downloading API JSON', errnote='Unable to download API page'):
        if not self._APP_INFO and not self._get_next_app_info():
            message = 'No working app info is available'
            if fatal:
                raise ExtractorError(message, expected=True)
            else:
                self.report_warning(message)
                return

        max_tries = len(self._APP_INFO_POOL) + 1  # _APP_INFO_POOL + _APP_INFO
        for count in itertools.count(1):
            self.write_debug(str(self._APP_INFO))
            real_query = self._build_api_query(query or {})
            try:
                return self._call_api_impl(
                    ep, video_id, query=real_query, data=data, headers=headers,
                    fatal=fatal, note=note, errnote=errnote)
            except ExtractorError as e:
                if isinstance(e.cause, json.JSONDecodeError) and e.cause.pos == 0:
                    message = str(e.cause or e.msg)
                    if not self._get_next_app_info():
                        if fatal:
                            raise
                        else:
                            self.report_warning(message)
                            return
                    self.report_warning(f'{message}. Retrying... (attempt {count} of {max_tries})')
                    continue
                raise