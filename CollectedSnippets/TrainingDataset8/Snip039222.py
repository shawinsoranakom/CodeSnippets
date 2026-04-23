def test_returns_all_expected_tabs(self):
        """Test that all labels are added in correct order."""
        tabs = st.tabs([f"tab {i}" for i in range(5)])

        self.assertEqual(len(tabs), 5)

        for tab in tabs:
            with tab:
                pass

        all_deltas = self.get_all_deltas_from_queue()

        tabs_block = all_deltas[1:]
        # 6 elements will be created: 1 horizontal block, 5 tabs
        self.assertEqual(len(all_deltas), 6)
        self.assertEqual(len(tabs_block), 5)
        for index, tabs_block in enumerate(tabs_block):
            self.assertEqual(tabs_block.add_block.tab.label, f"tab {index}")