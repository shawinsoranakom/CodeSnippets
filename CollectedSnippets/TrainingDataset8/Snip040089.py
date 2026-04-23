def test_st_header(self):
        """Test st.header."""
        st.header("some header")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some header")
        self.assertEqual(el.heading.tag, "h2")