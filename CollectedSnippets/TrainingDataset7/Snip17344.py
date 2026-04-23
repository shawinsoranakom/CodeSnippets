async def test_disconnect_both_return(self):
        # Force both the disconnect listener and the task that sends the
        # response to finish at the same time.
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request", "body": b"some body"})
        # Fetch response headers (this yields to asyncio and causes
        # ASGHandler.send_response() to dump the body of the response in the
        # queue).
        await communicator.receive_output()
        # Fetch response body (there's already some data queued up, so this
        # doesn't actually yield to the event loop, it just succeeds
        # instantly).
        await communicator.receive_output()
        # Send disconnect at the same time that response finishes (this just
        # puts some info in a queue, it doesn't have to yield to the event
        # loop).
        await communicator.send_input({"type": "http.disconnect"})
        # Waiting for the communicator _does_ yield to the event loop, since
        # ASGIHandler.send_response() is still waiting to do response.close().
        # It so happens that there are enough remaining yield points in both
        # tasks that they both finish while the loop is running.
        await communicator.wait()