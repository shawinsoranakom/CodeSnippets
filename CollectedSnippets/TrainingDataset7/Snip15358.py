def test_methods_with_multiple_arguments_display_arguments(self):
        """
        Methods with multiple arguments should have all their arguments
        displayed, but omitting 'self'.
        """
        self.assertContains(
            self.response, "<td>baz, rox, *some_args, **some_kwargs</td>"
        )
        self.assertContains(self.response, "<td>position_only_arg, arg, kwarg</td>")