def assertCallbackCalled(self, callback):
        id_field, user_field, data_field = UserSite._meta.fields
        expected_log = [
            (id_field, {"widget": CustomWidget}),
            (user_field, {}),
            (data_field, {"widget": CustomWidget, "localize": True}),
        ]
        self.assertEqual(callback.log, expected_log)