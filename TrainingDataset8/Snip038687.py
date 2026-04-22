def test_markdown(self):
        """Test Markdown element."""
        test_string = "    data         "

        st.markdown(test_string)

        element = self.get_delta_from_queue().new_element
        self.assertEqual("data", element.markdown.body)

        test_string = "    <a#data>data</a>   "
        st.markdown(test_string)
        element = self.get_delta_from_queue().new_element

        assert element.markdown.body.startswith("<a#data>")