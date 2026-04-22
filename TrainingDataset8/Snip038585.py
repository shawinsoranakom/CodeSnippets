def test_delete_option(self):
        # Create a dummy default option.
        config._create_option(
            "_test.testDeleteOption",
            description="This option tests the _delete_option function.",
            default_val="delete me!",
        )
        config.get_config_options(force_reparse=True)
        self.assertEqual(config.get_option("_test.testDeleteOption"), "delete me!")

        config._delete_option("_test.testDeleteOption")

        with pytest.raises(RuntimeError) as e:
            config.get_option("_test.testDeleteOption")
        self.assertEqual(
            str(e.value), 'Config key "_test.testDeleteOption" not defined.'
        )

        config._delete_option("_test.testDeleteOption")