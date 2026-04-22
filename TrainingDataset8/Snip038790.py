def test_checkbox_help_dedents(self):
        """Test that the checkbox help properly dedents in order to avoid code blocks"""
        st.checkbox(
            "Checkbox label",
            value=True,
            help="""\
hello
 world
""",
        )
        c = self.get_delta_from_queue(0).new_element.checkbox
        self.assertEqual(c.label, "Checkbox label")
        self.assertEqual(c.default, True)
        self.assertEqual(c.help, "hello\n world\n")