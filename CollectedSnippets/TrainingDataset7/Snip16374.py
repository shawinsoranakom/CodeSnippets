def test_initial_data_can_be_overridden(self):
        """
        The behavior for setting initial form data can be overridden in the
        ModelAdmin class. Usually, the initial value is set via the GET params.
        """
        response = self.client.get(
            reverse("admin:admin_views_restaurant_add", current_app=self.current_app),
            {"name": "test_value"},
        )
        # this would be the usual behavior
        self.assertNotContains(response, 'value="test_value"')
        # this is the overridden behavior
        self.assertContains(response, 'value="overridden_value"')