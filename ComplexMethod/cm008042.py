def wrapper(self, *args, **kwargs):
            while True:
                try:
                    return func(self, *args, **kwargs)
                except (CookieLoadError, DownloadCancelled, LazyList.IndexError, PagedList.IndexError):
                    raise
                except ReExtractInfo as e:
                    if e.expected:
                        self.to_screen(f'{e}; Re-extracting data')
                    else:
                        self.to_stderr('\r')
                        self.report_warning(f'{e}; Re-extracting data')
                    continue
                except GeoRestrictedError as e:
                    msg = e.msg
                    if e.countries:
                        msg += '\nThis video is available in {}.'.format(', '.join(
                            map(ISO3166Utils.short2full, e.countries)))
                    msg += '\nYou might want to use a VPN or a proxy server (with --proxy) to workaround.'
                    self.report_error(msg)
                except ExtractorError as e:  # An error we somewhat expected
                    self.report_error(str(e), e.format_traceback())
                except Exception as e:
                    if self.params.get('ignoreerrors'):
                        self.report_error(str(e), tb=encode_compat_str(traceback.format_exc()))
                    else:
                        raise
                break