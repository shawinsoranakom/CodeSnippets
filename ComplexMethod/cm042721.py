def _cb_bodyready(
        self, txresponse: TxResponse, request: Request
    ) -> _ResultT | Deferred[_ResultT]:
        if stop_download := check_stop_download(
            signals.headers_received,
            self._crawler,
            request,
            headers=self._headers_from_twisted_response(txresponse),
            body_length=txresponse.length,
        ):
            txresponse._transport.stopProducing()
            txresponse._transport.loseConnection()
            return {
                "txresponse": txresponse,
                "stop_download": stop_download,
            }

        # deliverBody hangs for responses without body
        if cast("int", txresponse.length) == 0:
            return {
                "txresponse": txresponse,
            }

        maxsize = request.meta.get("download_maxsize", self._maxsize)
        warnsize = request.meta.get("download_warnsize", self._warnsize)
        expected_size = (
            cast("int", txresponse.length)
            if txresponse.length != UNKNOWN_LENGTH
            else -1
        )
        fail_on_dataloss = request.meta.get(
            "download_fail_on_dataloss", self._fail_on_dataloss
        )

        if maxsize and expected_size > maxsize:
            warning_msg = get_maxsize_msg(
                expected_size, maxsize, request, expected=True
            )
            logger.warning(warning_msg)
            txresponse._transport.loseConnection()
            raise DownloadCancelledError(warning_msg)

        if warnsize and expected_size > warnsize:
            logger.warning(
                get_warnsize_msg(expected_size, warnsize, request, expected=True)
            )

        def _cancel(_: Any) -> None:
            # Abort connection immediately.
            txresponse._transport._producer.abortConnection()

        d: Deferred[_ResultT] = Deferred(_cancel)
        txresponse.deliverBody(
            _ResponseReader(
                finished=d,
                txresponse=txresponse,
                request=request,
                maxsize=maxsize,
                warnsize=warnsize,
                fail_on_dataloss=fail_on_dataloss,
                crawler=self._crawler,
                tls_verbose_logging=self._tls_verbose_logging,
            )
        )

        # save response for timeouts
        self._txresponse = txresponse

        return d