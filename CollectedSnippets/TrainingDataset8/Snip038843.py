def test_basic_func_with_doc(self):
        """Test basic function with docstring."""

        def my_func(some_param, another_param=123):
            """This is the doc"""
            pass

        st.help(my_func)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("my_func", ds.name)
        self.assertEqual("tests.streamlit.elements.help_test", ds.module)
        self.assertEqual("<class 'function'>", ds.type)
        self.assertEqual("(some_param, another_param=123)", ds.signature)
        self.assertEqual("This is the doc", ds.doc_string)