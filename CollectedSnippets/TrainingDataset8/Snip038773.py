def test_bokeh_version_failure(self):
        with patch("bokeh.__version__", return_value="2.4.0"):
            plot = figure()
            with self.assertRaises(StreamlitAPIException):
                st.bokeh_chart(plot)