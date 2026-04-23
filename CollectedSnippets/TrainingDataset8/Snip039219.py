def test_just_label(self):
        """Test that it can be called with no params"""
        expander = st.expander("label")

        with expander:
            pass

        expander_block = self.get_delta_from_queue()
        self.assertEqual(expander_block.add_block.expandable.label, "label")
        self.assertEqual(expander_block.add_block.expandable.expanded, False)