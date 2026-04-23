def dataReceived(self, bodyBytes: bytes) -> None:
        # This maybe called several times after cancel was called with buffered data.
        if self._finished.called:
            return

        assert self.transport
        self._bodybuf.write(bodyBytes)
        self._bytes_received += len(bodyBytes)

        if stop_download := check_stop_download(
            signals.bytes_received, self._crawler, self._request, data=bodyBytes
        ):
            self.transport.stopProducing()
            self.transport.loseConnection()
            self._finish_response(stop_download=stop_download)

        if self._maxsize and self._bytes_received > self._maxsize:
            logger.warning(
                get_maxsize_msg(
                    self._bytes_received, self._maxsize, self._request, expected=False
                )
            )
            # Clear buffer earlier to avoid keeping data in memory for a long time.
            self._bodybuf.truncate(0)
            self._finished.cancel()

        if (
            self._warnsize
            and self._bytes_received > self._warnsize
            and not self._reached_warnsize
        ):
            self._reached_warnsize = True
            logger.warning(
                get_warnsize_msg(
                    self._bytes_received, self._warnsize, self._request, expected=False
                )
            )