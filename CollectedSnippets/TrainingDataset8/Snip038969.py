def test_invalid_delta_color(self):
        with self.assertRaises(StreamlitAPIException) as exc:
            st.metric("Hello World.", 123, 0, "Invalid")

        self.assertEqual(
            "'Invalid' is not an accepted value. delta_color only accepts: "
            "'normal', 'inverse', or 'off'",
            str(exc.exception),
        )