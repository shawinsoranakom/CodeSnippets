def test_invalid_delta(self):
        with self.assertRaises(TypeError) as exc:
            st.metric("Testing", "123", [123])

        self.assertEqual(
            "'[123]' is of type <class 'list'>, which is not an accepted type."
            " delta only accepts: int, float, str, or None. Please convert the value to an accepted type.",
            str(exc.exception),
        )