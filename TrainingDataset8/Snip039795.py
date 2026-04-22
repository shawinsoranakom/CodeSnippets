def create_runtime_on_another_thread():
            try:
                # This function should be called in another thread, which
                # should not already have an asyncio loop.
                with self.assertRaises(BaseException):
                    asyncio.get_running_loop()

                # Create a Runtime instance and put it in the (thread-safe) queue,
                # so that the main thread can retrieve it safely. If Runtime
                # creation fails, we'll stick an Exception in the queue instead.
                config = RuntimeConfig(
                    "mock/script/path.py", "", media_file_storage=MagicMock()
                )
                queue.put(Runtime(config))
            except BaseException as e:
                queue.put(e)