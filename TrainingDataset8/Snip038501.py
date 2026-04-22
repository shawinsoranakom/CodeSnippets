def test_object_beta_warning_magic_function(self, mock_warning):
        """Test that we override dunder methods."""

        class DictClass(dict):
            pass

        beta_dict = object_beta_warning(DictClass(), "my_dict", "1980-01-01")

        expected_warning = (
            "Please replace `st.beta_my_dict` with `st.my_dict`.\n\n"
            "`st.beta_my_dict` will be removed after 1980-01-01."
        )

        beta_dict["foo"] = "bar"
        self.assertEqual(beta_dict["foo"], "bar")
        self.assertEqual(len(beta_dict), 1)
        self.assertEqual(list(beta_dict), ["foo"])

        # We only show the warning a single time for a given object.
        mock_warning.assert_called_once_with(expected_warning)