def test_doc_defined_for_type(self):
        """When the docs are defined for the type on an object, but not
        the object, we expect the docs of the type. This is the case
        of ndarray generated as follow.
        """

        array = np.arange(1)

        st.help(array)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("", ds.name)
        self.assertTrue("ndarray" in ds.doc_string)