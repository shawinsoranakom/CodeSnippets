def test_allowed_hosts(self):
        for type_ in (list, tuple):
            with self.subTest(type_=type_):
                allowed_hosts = type_("*")
                with mock.patch("django.test.utils._TestState") as x:
                    del x.saved_data
                    with self.settings(ALLOWED_HOSTS=allowed_hosts):
                        setup_test_environment()
                        self.assertEqual(settings.ALLOWED_HOSTS, ["*", "testserver"])