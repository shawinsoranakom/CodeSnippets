def test_server_option_changed(self, old, new, changed):
        old_options = create_config_options(old)
        new_options = create_config_options(new)
        self.assertEqual(
            config_util.server_option_changed(old_options, new_options), changed
        )