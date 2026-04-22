def test_help_dedents(self):
        """Test that help properly dedents"""
        st.text_area(
            "the label",
            value="TESTING",
            help="""\
        Hello World!
        This is a test


        """,
        )

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "TESTING")
        self.assertEqual(
            c.help,
            """Hello World!
This is a test


""",
        )