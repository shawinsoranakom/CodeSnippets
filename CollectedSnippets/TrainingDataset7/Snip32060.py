def check_spy_receiver_exit_calls(self, call_count):
        """
        Assert that `self.spy_receiver` was called exactly `call_count` times
        with the ``enter=False`` keyword argument.
        """
        kwargs_with_exit = [
            kwargs
            for args, kwargs in self.spy_receiver.call_args_list
            if ("enter", False) in kwargs.items()
        ]
        self.assertEqual(len(kwargs_with_exit), call_count)