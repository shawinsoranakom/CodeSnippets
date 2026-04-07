def test_register_type_handlers_connection(self):
        from django.contrib.postgres.signals import register_type_handlers

        self.assertNotIn(
            register_type_handlers, connection_created._live_receivers(None)[0]
        )
        with modify_settings(INSTALLED_APPS={"append": "django.contrib.postgres"}):
            self.assertIn(
                register_type_handlers, connection_created._live_receivers(None)[0]
            )
        self.assertNotIn(
            register_type_handlers, connection_created._live_receivers(None)[0]
        )