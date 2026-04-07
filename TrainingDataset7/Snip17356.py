async def test_read_body_thread(self):
        """Write runs on correct thread depending on rollover."""
        handler = ASGIHandler()
        loop_thread = threading.current_thread()

        called_threads = []

        def write_wrapper(data):
            called_threads.append(threading.current_thread())
            return original_write(data)

        # In-memory write (no rollover expected).
        in_memory_chunks = [
            {"type": "http.request", "body": b"small", "more_body": False}
        ]

        async def receive():
            return in_memory_chunks.pop(0)

        with tempfile.SpooledTemporaryFile(max_size=1024, mode="w+b") as temp_file:
            original_write = temp_file.write
            with (
                patch(
                    "django.core.handlers.asgi.tempfile.SpooledTemporaryFile",
                    return_value=temp_file,
                ),
                patch.object(temp_file, "write", side_effect=write_wrapper),
            ):
                await handler.read_body(receive)
        # Write was called in the event loop thread.
        self.assertIn(loop_thread, called_threads)

        # Clear thread log before next test.
        called_threads.clear()

        # Rollover to disk (write should occur in a threadpool thread).
        rolled_chunks = [
            {"type": "http.request", "body": b"A" * 16, "more_body": True},
            {"type": "http.request", "body": b"B" * 16, "more_body": False},
        ]

        async def receive_rolled():
            return rolled_chunks.pop(0)

        with (
            override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=10),
            tempfile.SpooledTemporaryFile(max_size=10, mode="w+b") as temp_file,
        ):
            original_write = temp_file.write
            # roll_over force in handlers.
            with (
                patch(
                    "django.core.handlers.asgi.tempfile.SpooledTemporaryFile",
                    return_value=temp_file,
                ),
                patch.object(temp_file, "write", side_effect=write_wrapper),
            ):
                await handler.read_body(receive_rolled)
        # The second write should have rolled over to disk.
        self.assertTrue(any(t != loop_thread for t in called_threads))