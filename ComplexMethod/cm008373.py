def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    self.to_screen('Extracting URL: %s' % (
                        url if self.get_param('verbose') else truncate_string(url, 100, 20)))
                    ie_result = self._real_extract(url)
                    if ie_result is None:
                        return None
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    subtitles = ie_result.get('subtitles') or {}
                    if 'no-live-chat' in self.get_param('compat_opts'):
                        for lang in ('live_chat', 'comments', 'danmaku'):
                            subtitles.pop(lang, None)
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except UnsupportedError:
            raise
        except ExtractorError as e:
            e.video_id = e.video_id or self.get_temp_id(url)
            e.ie = e.ie or self.IE_NAME
            e.traceback = e.traceback or sys.exc_info()[2]
            raise
        except IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e, expected=True, video_id=self.get_temp_id(url))
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e, video_id=self.get_temp_id(url))