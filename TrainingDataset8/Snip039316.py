def test_multithreaded_call_stack(self, _, call_stack):
        """CachedFunctionCallStack works across multiple threads."""

        def get_counter():
            return len(call_stack._cached_func_stack)

        def set_counter(val):
            call_stack._cached_func_stack = ["foo"] * val

        self.assertEqual(0, get_counter())
        set_counter(1)
        self.assertEqual(1, get_counter())

        values_in_thread = []

        def thread_test():
            values_in_thread.append(get_counter())
            set_counter(55)
            values_in_thread.append(get_counter())

        thread = ExceptionCapturingThread(target=thread_test)
        thread.start()
        thread.join()
        thread.assert_no_unhandled_exception()

        self.assertEqual([0, 55], values_in_thread)

        # The other thread should not have modified the main thread
        self.assertEqual(1, get_counter())