def test_callable_settings_forbidding_to_set_attributes(self):
        """
        Callable settings which forbid to set attributes should not break
        the debug page (#23070).
        """

        class CallableSettingWithSlots:
            __slots__ = []

            def __call__(self):
                return "This should not be displayed"

        with self.settings(DEBUG=True, WITH_SLOTS=CallableSettingWithSlots()):
            response = self.client.get("/raises500/")
            self.assertNotContains(
                response, "This should not be displayed", status_code=500
            )