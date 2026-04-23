def test_get_set_and_complex_config_options(self):
        """Verify that changing one option changes another, dependent one.

        This also implicitly tests simple and complex ConfigOptions as well as
        get_option() and set_option().
        """
        # Some useful variables.
        DUMMY_VAL_1, DUMMY_VAL_2, DUMMY_VAL_3 = "Steven", "Vincent", "Buscemi"

        # Set up both options.
        config._create_option(
            "_test.independentOption",
            description="This option can change at will",
            default_val=DUMMY_VAL_1,
        )

        @config._create_option("_test.dependentOption")
        def _test_dependent_option():
            """Depend on the value of _test.independentOption."""
            return config.get_option("_test.independentOption")

        config.get_config_options(force_reparse=True)

        # Check that the default values are good.
        self.assertEqual(config.get_option("_test.independentOption"), DUMMY_VAL_1)
        self.assertEqual(config.get_option("_test.dependentOption"), DUMMY_VAL_1)
        self.assertEqual(
            config.get_where_defined("_test.independentOption"),
            ConfigOption.DEFAULT_DEFINITION,
        )
        self.assertEqual(
            config.get_where_defined("_test.dependentOption"),
            ConfigOption.DEFAULT_DEFINITION,
        )

        # Override the independent option. Both update!
        config.set_option("_test.independentOption", DUMMY_VAL_2)
        self.assertEqual(config.get_option("_test.independentOption"), DUMMY_VAL_2)
        self.assertEqual(config.get_option("_test.dependentOption"), DUMMY_VAL_2)
        self.assertEqual(
            config.get_where_defined("_test.independentOption"), config._USER_DEFINED
        )
        self.assertEqual(
            config.get_where_defined("_test.dependentOption"),
            ConfigOption.DEFAULT_DEFINITION,
        )

        # Override the dependent option. Only that updates!
        config.set_option("_test.dependentOption", DUMMY_VAL_3)
        self.assertEqual(config.get_option("_test.independentOption"), DUMMY_VAL_2)
        self.assertEqual(config.get_option("_test.dependentOption"), DUMMY_VAL_3)
        self.assertEqual(
            config.get_where_defined("_test.independentOption"), config._USER_DEFINED
        )
        self.assertEqual(
            config.get_where_defined("_test.dependentOption"), config._USER_DEFINED
        )