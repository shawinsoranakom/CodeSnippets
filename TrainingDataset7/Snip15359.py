def test_instance_of_property_methods_are_displayed(self):
        """Model properties are displayed as fields."""
        self.assertContains(self.response, "<td>a_property</td>")