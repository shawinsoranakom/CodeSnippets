def __call__(self, environ):
        # Set up middleware if needed. We couldn't do this earlier, because
        # settings weren't available.
        if self._middleware_chain is None:
            self.load_middleware()

        request_started.disconnect(close_old_connections)
        request_started.send(sender=self.__class__, environ=environ)
        request_started.connect(close_old_connections)
        request = WSGIRequest(environ)
        # sneaky little hack so that we can easily get round
        # CsrfViewMiddleware. This makes life easier, and is probably
        # required for backwards compatibility with external tests against
        # admin views.
        request._dont_enforce_csrf_checks = not self.enforce_csrf_checks

        # Request goes through middleware.
        response = self.get_response(request)

        # Simulate behaviors of most web servers.
        conditional_content_removal(request, response)

        # Attach the originating request to the response so that it could be
        # later retrieved.
        response.wsgi_request = request

        # Emulate a WSGI server by calling the close method on completion.
        if response.streaming:
            if response.is_async:
                response.streaming_content = aclosing_iterator_wrapper(
                    response.streaming_content, response.close
                )
            else:
                response.streaming_content = closing_iterator_wrapper(
                    response.streaming_content, response.close
                )
        else:
            request_finished.disconnect(close_old_connections)
            response.close()  # will fire request_finished
            request_finished.connect(close_old_connections)

        return response