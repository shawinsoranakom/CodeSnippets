def test_invalid_label(self):
        with self.assertRaises(TypeError) as exc:
            st.metric(123, "-321")

        self.assertEqual(
            "'123' is of type <class 'int'>, which is not an accepted type."
            " label only accepts: str. Please convert the label to an accepted type.",
            str(exc.exception),
        )