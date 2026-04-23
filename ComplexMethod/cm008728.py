def _parse_time_text(self, text, report_failure=True):
        if not text:
            return
        dt_ = self.extract_relative_time(text)
        timestamp = None
        if isinstance(dt_, dt.datetime):
            timestamp = calendar.timegm(dt_.timetuple())

        if timestamp is None:
            timestamp = (
                unified_timestamp(text) or unified_timestamp(
                    self._search_regex(
                        (r'([a-z]+\s*\d{1,2},?\s*20\d{2})', r'(?:.+|^)(?:live|premieres|ed|ing)(?:\s*(?:on|for))?\s*(.+\d)'),
                        text.lower(), 'time text', default=None)))

        if report_failure and text and timestamp is None and self._preferred_lang in (None, 'en'):
            self.report_warning(
                f'Cannot parse localized time text "{text}"', only_once=True)
        return timestamp