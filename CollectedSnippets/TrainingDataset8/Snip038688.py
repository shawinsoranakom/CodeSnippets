def test_code(self):
        """Test st.code()"""
        code = "print('Hello, %s!' % 'Streamlit')"
        expected_body = "```python\n%s\n```" % code

        st.code(code, language="python")
        element = self.get_delta_from_queue().new_element

        # st.code() creates a MARKDOWN text object that wraps
        # the body inside a codeblock declaration
        self.assertEqual(element.markdown.body, expected_body)