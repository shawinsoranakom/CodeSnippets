def test_methods_with_arguments_display_arguments(self):
        """
        Methods with arguments should have their arguments displayed.
        """
        self.assertContains(self.response, "<td>new_name</td>")
        self.assertContains(self.response, "<td>keyword_only_arg</td>")