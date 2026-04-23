def close(
        self,
        reason: StreamCloseReason,
        errors: Sequence[BaseException] | None = None,
        from_protocol: bool = False,
    ) -> None:
        """Based on the reason sent we will handle each case."""
        if self.metadata["stream_closed_server"]:
            raise StreamClosedError(self.stream_id)

        if not isinstance(reason, StreamCloseReason):
            raise TypeError(
                f"Expected StreamCloseReason, received {reason.__class__.__qualname__}"
            )

        # Have default value of errors as an empty list as
        # some cases can add a list of exceptions
        errors = errors or ()

        if not from_protocol:
            self._protocol.pop_stream(self.stream_id)

        self.metadata["stream_closed_server"] = True

        # We do not check for Content-Length or Transfer-Encoding in response headers
        # and add `partial` flag as in HTTP/1.1 as 'A request or response that includes
        # a payload body can include a content-length header field' (RFC 7540 - Section 8.1.2.6)

        # NOTE: Order of handling the events is important here
        # As we immediately cancel the request when maxsize is exceeded while
        # receiving DATA_FRAME's when we have received the headers (not
        # having Content-Length)
        if reason in {
            StreamCloseReason.MAXSIZE_EXCEEDED,
            StreamCloseReason.MAXSIZE_EXCEEDED_ACTUAL,
        }:
            expected_size = int(
                self._response["headers"].get(
                    b"Content-Length", self._response["flow_controlled_size"]
                )
            )
            error_msg = get_maxsize_msg(
                expected_size,
                self._download_maxsize,
                self._request,
                expected=reason == StreamCloseReason.MAXSIZE_EXCEEDED,
            )
            logger.error(error_msg)
            self._deferred_response.errback(DownloadCancelledError(error_msg))

        elif reason is StreamCloseReason.ENDED:
            self._fire_response_deferred()

        # Stream was abruptly ended here
        elif reason is StreamCloseReason.CANCELLED:
            # Client has cancelled the request. Remove all the data
            # received and fire the response deferred with no flags set

            # NOTE: The data is already flushed in Stream.reset_stream() called
            # immediately when the stream needs to be cancelled

            # There maybe no :status in headers, we make
            # HTTP Status Code: 499 - Client Closed Request
            if self._response["status"] is None:
                self._response["status"] = 499
            self._fire_response_deferred()

        elif reason is StreamCloseReason.RESET:
            self._deferred_response.errback(
                ResponseFailed(
                    [
                        Failure(
                            f"Remote peer {self._protocol.metadata['ip_address']} sent RST_STREAM",
                            ProtocolError,
                        )
                    ]
                )
            )

        elif reason is StreamCloseReason.CONNECTION_LOST:
            self._deferred_response.errback(ResponseFailed(errors))

        elif reason is StreamCloseReason.INACTIVE:
            errors = (InactiveStreamClosed(self._request), *errors)
            self._deferred_response.errback(ResponseFailed(errors))

        else:
            assert reason is StreamCloseReason.INVALID_HOSTNAME
            self._deferred_response.errback(
                InvalidHostname(
                    self._request,
                    str(self._protocol.metadata["uri"].host, "utf-8"),
                    f"{self._protocol.metadata['ip_address']}:{self._protocol.metadata['uri'].port}",
                )
            )