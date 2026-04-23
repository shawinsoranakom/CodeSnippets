def test_correct_translatable_file_locale_dir(self):

        class ReturnTrackingMock(mock.Mock):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.call_return_value_list = []

            def __call__(self, *args, **kwargs):
                value = super().__call__(*args, **kwargs)
                self.call_return_value_list.append(value)
                return value

        for locale_paths in [
            [],
            [
                os.path.join(self.test_dir, "app_with_locale", "locale"),
            ],
            [
                os.path.join(self.test_dir, "locale"),
                os.path.join(self.test_dir, "app_with_locale", "locale"),
            ],
        ]:
            with self.subTest(locale_paths=locale_paths):
                with override_settings(LOCALE_PATHS=locale_paths):
                    cmd = MakeMessagesCommand()
                    rtm = ReturnTrackingMock(wraps=cmd.find_files)

                    with mock.patch.object(cmd, "find_files", new=rtm):
                        management.call_command(cmd, locale=["en", "ru"], verbosity=0)
                        self.assertEqual(len(rtm.call_args_list), 1)
                        self.assertEqual(len(rtm.call_return_value_list), 1)

                        for tf in rtm.call_return_value_list[0]:
                            self.assertIsInstance(tf, TranslatableFile)
                            abs_file_path = os.path.abspath(
                                os.path.join(self.test_dir, tf.dirpath, tf.file)
                            )
                            max_common_path = max(
                                [
                                    os.path.commonpath([abs_file_path, locale_path])
                                    for locale_path in cmd.locale_paths
                                ],
                                key=len,
                            )
                            correct_locale_dir = os.path.join(max_common_path, "locale")
                            self.assertEqual(tf.locale_dir, correct_locale_dir)