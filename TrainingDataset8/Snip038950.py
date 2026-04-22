def test_default_map_copy(self):
        """Test that _DEFAULT_MAP is not modified as other work occurs."""
        self.assertEqual(_DEFAULT_MAP["initialViewState"]["latitude"], 0)

        st.map(df1)
        self.assertEqual(_DEFAULT_MAP["initialViewState"]["latitude"], 0)