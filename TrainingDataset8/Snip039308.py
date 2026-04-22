def test_without_spinner(self, _, cache_decorator):
        """If the show_spinner flag is not set, the report queue should be
        empty.
        """

        @cache_decorator(show_spinner=False)
        def function_without_spinner(x: int) -> int:
            return x

        function_without_spinner(3)
        self.assertTrue(self.forward_msg_queue.is_empty())