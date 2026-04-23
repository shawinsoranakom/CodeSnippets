def read(self, amt=None):
        if self.closed:
            return b''
        try:
            data = self.fp.read(amt)
            underlying = getattr(self.fp, 'fp', None)
            if isinstance(self.fp, http.client.HTTPResponse) and underlying is None:
                # http.client.HTTPResponse automatically closes itself when fully read
                self.close()
            elif isinstance(self.fp, urllib.response.addinfourl) and underlying is not None:
                # urllib's addinfourl does not close the underlying fp automatically when fully read
                if isinstance(underlying, io.BytesIO):
                    # data URLs or in-memory responses (e.g. gzip/deflate/brotli decoded)
                    if underlying.tell() >= len(underlying.getbuffer()):
                        self.close()
                elif isinstance(underlying, io.BufferedReader) and amt is None:
                    # file URLs.
                    # XXX: this will not mark the response as closed if it was fully read with amt.
                    self.close()
            elif underlying is not None and underlying.closed:
                # Catch-all for any cases where underlying file is closed
                self.close()
            return data
        except Exception as e:
            handle_response_read_exceptions(e)
            raise e