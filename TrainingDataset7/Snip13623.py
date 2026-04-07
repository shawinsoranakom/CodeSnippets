async def __call__(self, scope):
        # Set up middleware if needed. We couldn't do this earlier, because
        # settings weren't available.
        if self._middleware_chain is None:
            self.load_middleware(is_async=True)
        # Extract body file from the scope, if provided.
        if "_body_file" in scope:
            body_file = scope.pop("_body_file")
        else:
            body_file = FakePayload("")

        request_started.disconnect(close_old_connections)
        await request_started.asend(sender=self.__class__, scope=scope)
        request_started.connect(close_old_connections)
        # Wrap FakePayload body_file to allow large read() in test environment.
        request = ASGIRequest(scope, LimitedStream(body_file, len(body_file)))
        # Sneaky little hack so that we can easily get round
        # CsrfViewMiddleware. This makes life easier, and is probably required
        # for backwards compatibility with external tests against admin views.
        request._dont_enforce_csrf_checks = not self.enforce_csrf_checks
        # Request goes through middleware.
        response = await self.get_response_async(request)
        # Simulate behaviors of most web servers.
        conditional_content_removal(request, response)
        # Attach the originating ASGI request to the response so that it could
        # be later retrieved.
        response.asgi_request = request
        # Emulate a server by calling the close method on completion.
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
            # Will fire request_finished.
            await sync_to_async(response.close, thread_sensitive=False)()
            request_finished.connect(close_old_connections)
        return response