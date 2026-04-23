def test_function_beta_warning(self, mock_warning):
        def multiply(a, b):
            return a * b

        beta_multiply = function_beta_warning(multiply, "1980-01-01")

        self.assertEqual(beta_multiply(3, 2), 6)
        mock_warning.assert_called_once_with(
            "Please replace `st.beta_multiply` with `st.multiply`.\n\n"
            "`st.beta_multiply` will be removed after 1980-01-01."
        )