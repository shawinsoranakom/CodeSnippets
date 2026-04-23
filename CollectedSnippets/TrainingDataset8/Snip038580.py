def test_cannot_overwrite_config_key(self):
        """Test overwriting a config option using _create_option."""
        with self.assertRaises(AssertionError):
            config._create_option("_test.overwriteKey")
            config._create_option("_test.overwriteKey")