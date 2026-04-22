def test_st_code(self):
        """Test st.code."""
        st.code("print('My string = %d' % my_value)", language="python")
        expected = textwrap.dedent(
            """
            ```python
            print('My string = %d' % my_value)
            ```
        """
        )

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, expected.strip())