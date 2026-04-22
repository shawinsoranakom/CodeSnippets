def test_complex_config_option_must_have_doc_strings(self):
        """Test that complex config options use funcs with doc stringsself.

        This is because the doc string forms the option's description.
        """
        with self.assertRaises(AssertionError):

            @ConfigOption("_test.noDocString")
            def no_doc_string():
                pass