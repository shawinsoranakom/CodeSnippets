def test_without_spinner(self):
        """If the show_spinner flag is not set, the report queue should be
        empty.
        """
        function_without_spinner()
        self.assertTrue(self.forward_msg_queue.is_empty())