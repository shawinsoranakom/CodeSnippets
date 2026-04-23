def connectionLost(self, reason: Failure = connectionDone) -> None:
        if self._finished.called:
            return

        if reason.check(ResponseDone):
            self._finish_response()
            return

        if reason.check(PotentialDataLoss):
            self._finish_response(flags=["partial"])
            return

        if reason.check(ResponseFailed) and any(
            r.check(_DataLoss)
            for r in reason.value.reasons  # type: ignore[union-attr]
        ):
            if not self._fail_on_dataloss:
                self._finish_response(flags=["dataloss"])
                return

            exc = ResponseDataLossError()
            exc.__cause__ = reason.value
            reason = Failure(exc)

        self._finished.errback(reason)