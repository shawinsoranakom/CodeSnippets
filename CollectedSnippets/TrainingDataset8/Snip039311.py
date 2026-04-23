def test_with_empty_text_spinner(self, _, cache_decorator):
        """If the show_spinner flag is set, even if it is empty text,
        there should be one element in the report queue.
        """

        @cache_decorator(show_spinner="")
        def function_with_spinner_empty_text(x: int) -> int:
            return x

        function_with_spinner_empty_text(3)
        self.assertFalse(self.forward_msg_queue.is_empty())