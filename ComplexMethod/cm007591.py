def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url)
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except ExtractorError:
            raise
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e, expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e)