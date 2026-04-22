def test_with_custom_text_spinner(self, _, cache_decorator):
        """If the show_spinner flag is set, there should be one element in the
        report queue.
        """

        @cache_decorator(show_spinner="CUSTOM_TEXT")
        def function_with_spinner_custom_text(x: int) -> int:
            return x

        function_with_spinner_custom_text(3)
        self.assertFalse(self.forward_msg_queue.is_empty())