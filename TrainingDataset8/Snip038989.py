def test_over_max_selections_initialization(self):
        with self.assertRaises(StreamlitAPIException) as e:
            st.multiselect(
                "the label", ["a", "b", "c", "d"], ["a", "b", "c"], max_selections=2
            )
        self.assertEqual(
            str(e.exception),
            """
Multiselect has 3 options selected but `max_selections`
is set to 2. This happened because you either gave too many options to `default`
or you manipulated the widget's state through `st.session_state`. Note that
the latter can happen before the line indicated in the traceback.
Please select at most 2 options.
""",
        )