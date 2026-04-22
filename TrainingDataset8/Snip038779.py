def test_with_spinner(self):
        """If the show_spinner flag is set, there should be one element in the
        report queue.
        """
        function_with_spinner()
        self.assertFalse(self.forward_msg_queue.is_empty())