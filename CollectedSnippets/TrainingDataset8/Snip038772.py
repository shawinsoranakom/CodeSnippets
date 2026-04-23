def test_figure(self):
        """Test that it can be called with figure."""
        plot = figure()
        plot.line([1], [1])
        st.bokeh_chart(plot)

        c = self.get_delta_from_queue().new_element.bokeh_chart
        self.assertEqual(hasattr(c, "figure"), True)