def test_bad_persist_value(self):
        """Throw an error if an invalid value is passed to 'persist'."""
        with self.assertRaises(StreamlitAPIException) as e:

            @st.experimental_memo(persist="yesplz")
            def foo():
                pass

        self.assertEqual(
            "Unsupported persist option 'yesplz'. Valid values are 'disk' or None.",
            str(e.exception),
        )