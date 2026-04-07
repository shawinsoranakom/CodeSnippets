async def handle(self, scope, receive, send):
        """
        Handles the ASGI request. Called via the __call__ method.
        """
        # Receive the HTTP request body as a stream object.
        try:
            body_file = await self.read_body(receive)
        except RequestAborted:
            return

        with closing(body_file):
            # Request is complete and can be served.
            set_script_prefix(get_script_prefix(scope))
            await signals.request_started.asend(sender=self.__class__, scope=scope)
            # Get the request and check for basic issues.
            request, error_response = self.create_request(scope, body_file)
            if request is None:
                body_file.close()
                await self.send_response(error_response, send)
                await sync_to_async(error_response.close)()
                return

            class RequestProcessed(Exception):
                pass

            response = None
            try:
                try:
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self.listen_for_disconnect(receive))
                        response = await self.run_get_response(request)
                        await self.send_response(response, send)
                        raise RequestProcessed
                except* (RequestProcessed, RequestAborted):
                    pass
            except BaseExceptionGroup as exception_group:
                if len(exception_group.exceptions) == 1:
                    raise exception_group.exceptions[0]
                raise

            if response is None:
                await signals.request_finished.asend(sender=self.__class__)
            else:
                await sync_to_async(response.close)()