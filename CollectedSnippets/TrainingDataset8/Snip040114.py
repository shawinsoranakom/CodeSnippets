def test_st_alert_exceptions(self, alert_func):
        """Test that alert functions throw an exception when a non-emoji is given as an icon."""
        with self.assertRaises(StreamlitAPIException):
            alert_func("some alert", icon="hello world")