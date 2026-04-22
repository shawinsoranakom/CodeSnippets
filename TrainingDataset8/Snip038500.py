def test_object_beta_warning(self, mock_warning):
        class Multiplier:
            def multiply(self, a, b):
                return a * b

        beta_multiplier = object_beta_warning(Multiplier(), "multiplier", "1980-01-01")

        expected_warning = (
            "Please replace `st.beta_multiplier` with `st.multiplier`.\n\n"
            "`st.beta_multiplier` will be removed after 1980-01-01."
        )

        self.assertEqual(beta_multiplier.multiply(3, 2), 6)
        self.assertEqual(beta_multiplier.multiply(5, 4), 20)

        # We only show the warning a single time for a given object.
        mock_warning.assert_called_once_with(expected_warning)