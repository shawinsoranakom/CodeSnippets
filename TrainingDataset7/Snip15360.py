def test_instance_of_cached_property_methods_are_displayed(self):
        """Model cached properties are displayed as fields."""
        self.assertContains(self.response, "<td>a_cached_property</td>")