def test_set_log_level_error(self):
        """Test streamlit.logger.set_log_level."""
        with pytest.raises(SystemExit) as e:
            logger.set_log_level(90)
        self.assertEqual(e.type, SystemExit)
        self.assertEqual(e.value.code, 1)