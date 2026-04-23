def getresponse(self):
        """Get the response from the server.

        If the HTTPConnection is in the correct state, returns an
        instance of HTTPResponse.

        If a request has not been sent or if a previous response has
        not be handled, ResponseNotReady is raised.  If the HTTP
        response indicates that the connection should be closed, then
        it will be closed before the response is returned.  When the
        connection is closed, the underlying socket is closed.
        """

        # if a prior response has been completed, then forget about it.
        if self.__response and self.__response.isclosed():
            self.__response = None

        # if a prior response exists, then it must be completed (otherwise, we
        # cannot read this response's header to determine the connection-close
        # behavior)
        #
        # note: if a prior response existed, but was connection-close, then the
        # socket and response were made independent of this HTTPConnection
        # object since a new request requires that we open a whole new
        # connection
        #
        # this means the prior response had one of two states:
        #   1) will_close: this connection was reset and the prior socket and
        #                  response operate independently
        #   2) persistent: the response was retained and we await its
        #                  isclosed() status to become true.
        #
        if self.__state != _CS_REQ_SENT or self.__response:
            raise ResponseNotReady(self.__state)

        if self.debuglevel > 0:
            response = self.response_class(self.sock, self.debuglevel,
                                           method=self._method)
        else:
            response = self.response_class(self.sock, method=self._method)

        try:
            try:
                if self.max_response_headers is None:
                    response.begin()
                else:
                    response.begin(_max_headers=self.max_response_headers)
            except ConnectionError:
                self.close()
                raise
            assert response.will_close != _UNKNOWN
            self.__state = _CS_IDLE

            if response.will_close:
                # this effectively passes the connection to the response
                self.close()
            else:
                # remember this, so we can tell when it is complete
                self.__response = response

            return response
        except:
            response.close()
            raise