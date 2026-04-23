def test_middleware_loaded_only_once(self):
        command = runserver.Command()
        with mock.patch("django.middleware.common.CommonMiddleware") as mocked:
            command.get_handler(use_static_handler=True, insecure_serving=True)
            self.assertEqual(mocked.call_count, 1)