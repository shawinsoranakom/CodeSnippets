def test_arrow_is_default(self):
        """The 'arrow' config option is the default."""
        self.assertEqual("arrow", streamlit.get_option("global.dataFrameSerialization"))