def test_st_markdown(self):
        """Test st.markdown."""
        st.markdown("    some markdown  ")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, "some markdown")

        # test the unsafe_allow_html keyword
        st.markdown("    some markdown  ", unsafe_allow_html=True)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, "some markdown")
        self.assertTrue(el.markdown.allow_html)