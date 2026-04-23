def test_accept_valid_formats(self):
        # note: We decided to accept %u even though it is slightly problematic.
        #       See https://github.com/streamlit/streamlit/pull/943
        SUPPORTED = "adifFeEgGuXxo"
        for char in SUPPORTED:
            st.number_input("any label", format="%" + char)
            c = self.get_delta_from_queue().new_element.number_input
            self.assertEqual(c.format, "%" + char)