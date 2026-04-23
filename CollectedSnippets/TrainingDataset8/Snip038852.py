def test_doc_type_is_type(self):
        """When the type of the object is type and no docs are defined,
        we expect docs are not available"""

        class MyClass(object):
            pass

        st.help(MyClass)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual(type(MyClass), type)
        self.assertEqual("MyClass", ds.name)
        self.assertEqual("tests.streamlit.elements.help_test", ds.module)
        self.assertEqual("No docs available.", ds.doc_string)