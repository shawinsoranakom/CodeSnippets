def test_callable_settings(self):
        """
        Callable settings should not be evaluated in the debug page (#21345).
        """

        def callable_setting():
            return "This should not be displayed"

        with self.settings(DEBUG=True, FOOBAR=callable_setting):
            response = self.client.get("/raises500/")
            self.assertNotContains(
                response, "This should not be displayed", status_code=500
            )