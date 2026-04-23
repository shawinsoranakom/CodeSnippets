def test_st_balloons(self):
        """Test st.balloons."""
        st.balloons()
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.balloons.show, True)