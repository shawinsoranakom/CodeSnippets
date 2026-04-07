async def test_cancel_post_request_with_sync_processing(self):
        """
        The request.body object should be available and readable in view
        code, even if the ASGIHandler cancels processing part way through.
        """
        loop = asyncio.get_event_loop()
        # Events to monitor the view processing from the parent test code.
        view_started_event = asyncio.Event()
        view_finished_event = asyncio.Event()
        # Record received request body or exceptions raised in the test view
        outcome = []

        # This view will run in a new thread because it is wrapped in
        # sync_to_async. The view consumes the POST body data after a short
        # delay. The test will cancel the request using http.disconnect during
        # the delay, but because this is a sync view the code runs to
        # completion. There should be no exceptions raised inside the view
        # code.
        @csrf_exempt
        @sync_to_async
        def post_view(request):
            try:
                loop.call_soon_threadsafe(view_started_event.set)
                time.sleep(0.1)
                # Do something to read request.body after pause
                outcome.append({"request_body": request.body})
                return HttpResponse("ok")
            except Exception as e:
                outcome.append({"exception": e})
            finally:
                loop.call_soon_threadsafe(view_finished_event.set)

        # Request class to use the view.
        class TestASGIRequest(ASGIRequest):
            urlconf = (path("post/", post_view),)

        # Handler to use request class.
        class TestASGIHandler(ASGIHandler):
            request_class = TestASGIRequest

        application = TestASGIHandler()
        scope = self.async_request_factory._base_scope(
            method="POST",
            path="/post/",
        )
        communicator = ApplicationCommunicator(application, scope)

        await communicator.send_input({"type": "http.request", "body": b"Body data!"})

        # Wait until the view code has started, then send http.disconnect.
        await view_started_event.wait()
        await communicator.send_input({"type": "http.disconnect"})
        # Wait until view code has finished.
        await view_finished_event.wait()
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output()

        self.assertEqual(outcome, [{"request_body": b"Body data!"}])