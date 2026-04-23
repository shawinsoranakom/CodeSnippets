def test_methods_with_arguments_display_arguments_default_value(self):
        """
        Methods with keyword arguments should have their arguments displayed.
        """
        self.assertContains(self.response, "<td>suffix=&#x27;ltd&#x27;</td>")