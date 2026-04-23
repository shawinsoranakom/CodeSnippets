def test_starts_thread_with_args(self, mocked_check_errors, mocked_thread):
        fake_reloader = mock.MagicMock()
        fake_main_func = mock.MagicMock()
        fake_thread = mock.MagicMock()
        mocked_check_errors.return_value = fake_main_func
        mocked_thread.return_value = fake_thread
        autoreload.start_django(fake_reloader, fake_main_func, 123, abc=123)
        self.assertEqual(mocked_thread.call_count, 1)
        self.assertEqual(
            mocked_thread.call_args[1],
            {
                "target": fake_main_func,
                "args": (123,),
                "kwargs": {"abc": 123},
                "name": "django-main-thread",
            },
        )
        self.assertIs(fake_thread.daemon, True)
        self.assertTrue(fake_thread.start.called)