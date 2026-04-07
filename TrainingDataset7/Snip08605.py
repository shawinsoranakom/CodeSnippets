async def _get_response_async(self, request):
        """
        Resolve and call the view, then apply view, exception, and
        template_response middleware. This method is everything that happens
        inside the request/response middleware.
        """
        response = None
        callback, callback_args, callback_kwargs = self.resolve_request(request)

        # Apply view middleware.
        for middleware_method in self._view_middleware:
            response = await middleware_method(
                request, callback, callback_args, callback_kwargs
            )
            if response:
                break

        if response is None:
            wrapped_callback = self.make_view_atomic(callback)
            # If it is a synchronous view, run it in a subthread
            if not iscoroutinefunction(wrapped_callback):
                wrapped_callback = sync_to_async(
                    wrapped_callback, thread_sensitive=True
                )
            try:
                response = await wrapped_callback(
                    request, *callback_args, **callback_kwargs
                )
            except Exception as e:
                response = await sync_to_async(
                    self.process_exception_by_middleware,
                    thread_sensitive=True,
                )(e, request)
                if response is None:
                    raise

        # Complain if the view returned None or an uncalled coroutine.
        self.check_response(response, callback)

        # If the response supports deferred rendering, apply template
        # response middleware and then render the response
        if hasattr(response, "render") and callable(response.render):
            for middleware_method in self._template_response_middleware:
                response = await middleware_method(request, response)
                # Complain if the template response middleware returned None or
                # an uncalled coroutine.
                self.check_response(
                    response,
                    middleware_method,
                    name="%s.process_template_response"
                    % (middleware_method.__self__.__class__.__name__,),
                )
            try:
                if iscoroutinefunction(response.render):
                    response = await response.render()
                else:
                    response = await sync_to_async(
                        response.render, thread_sensitive=True
                    )()
            except Exception as e:
                response = await sync_to_async(
                    self.process_exception_by_middleware,
                    thread_sensitive=True,
                )(e, request)
                if response is None:
                    raise

        # Make sure the response is not a coroutine
        if asyncio.iscoroutine(response):
            raise RuntimeError("Response is still a coroutine.")
        return response