async def test_concurrent_async_uses_multiple_thread_pools(self):
        sync_waiter.active_threads.clear()

        # Send 2 requests concurrently
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/wait/")
        communicators = []
        for _ in range(2):
            communicators.append(ApplicationCommunicator(application, scope))
            await communicators[-1].send_input({"type": "http.request"})

        # Each request must complete with a status code of 200
        # If requests aren't scheduled concurrently, the barrier in the
        # sync_wait view will time out, resulting in a 500 status code.
        for communicator in communicators:
            response_start = await communicator.receive_output()
            self.assertEqual(response_start["type"], "http.response.start")
            self.assertEqual(response_start["status"], 200)
            response_body = await communicator.receive_output()
            self.assertEqual(response_body["type"], "http.response.body")
            self.assertEqual(response_body["body"], b"Hello World!")
            # Give response.close() time to finish.
            await communicator.wait()

        # The requests should have scheduled on different threads. Note
        # active_threads is a set (a thread can only appear once), therefore
        # length is a sufficient check.
        self.assertEqual(len(sync_waiter.active_threads), 2)

        sync_waiter.active_threads.clear()