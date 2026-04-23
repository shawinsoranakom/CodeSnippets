def test_location_empty(self):
        msg = "without having set the STATIC_ROOT setting to a filesystem path"
        err = StringIO()
        for root in ["", None]:
            with override_settings(STATIC_ROOT=root):
                with self.assertRaisesMessage(ImproperlyConfigured, msg):
                    call_command(
                        "collectstatic", interactive=False, verbosity=0, stderr=err
                    )