def test_with_spinner(self, _, cache_decorator):
        """If the show_spinner flag is set, there should be one element in the
        report queue.
        """

        @cache_decorator(show_spinner=True)
        def function_with_spinner(x: int) -> int:
            return x

        function_with_spinner(3)
        self.assertFalse(self.forward_msg_queue.is_empty())