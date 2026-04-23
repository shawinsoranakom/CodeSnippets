def send_header(self, keyword, value):
        if keyword.casefold() == 'date':
            if self._sent_date_header is None:
                self._sent_date_header = value
            elif self._sent_date_header == value:
                return  # don't send the same header twice
            else:
                sent_datetime = parsedate_to_datetime(self._sent_date_header)
                new_datetime = parsedate_to_datetime(value)
                if sent_datetime == new_datetime:
                    return  # don't send the same date twice (differ in format)
                if abs((sent_datetime - new_datetime).total_seconds()) <= 1:
                    return  # don't send the same date twice (jitter of 1 second)
                _logger.warning(
                    "sending two different Date response headers: %r vs %r",
                    self._sent_date_header, value)

        if keyword.casefold() == 'server':
            if self._sent_server_header is None:
                self._sent_server_header = value
            elif self._sent_server_header == value:
                return  # don't send the same header twice
            else:
                _logger.warning(
                    "sending two different Server response headers: %r vs %r",
                    self._sent_server_header, value)

        return super().send_header(keyword, value)