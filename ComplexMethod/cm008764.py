def read(self, amt: int | None = None):
        try:
            data = self._real_read(amt)
            if self.fp.closed:
                self.close()
            return data
        # See urllib3.response.HTTPResponse.read() for exceptions raised on read
        except urllib3.exceptions.SSLError as e:
            raise SSLError(cause=e) from e

        except urllib3.exceptions.ProtocolError as e:
            # IncompleteRead is always contained within ProtocolError
            # See urllib3.response.HTTPResponse._error_catcher()
            ir_err = next(
                (err for err in (e.__context__, e.__cause__, *variadic(e.args))
                 if isinstance(err, http.client.IncompleteRead)), None)
            if ir_err is not None:
                # `urllib3.exceptions.IncompleteRead` is subclass of `http.client.IncompleteRead`
                # but uses an `int` for its `partial` property.
                partial = ir_err.partial if isinstance(ir_err.partial, int) else len(ir_err.partial)
                raise IncompleteRead(partial=partial, expected=ir_err.expected) from e
            raise TransportError(cause=e) from e

        except urllib3.exceptions.HTTPError as e:
            # catch-all for any other urllib3 response exceptions
            raise TransportError(cause=e) from e