def test_invalid_value(self):
        with self.assertRaises(TypeError) as exc:
            st.metric("Testing", [1, 2, 3])

        self.assertEqual(
            "'[1, 2, 3]' is of type <class 'list'>, which is not an accepted type."
            " value only accepts: int, float, str, or None. Please convert the value to an accepted type.",
            str(exc.exception),
        )