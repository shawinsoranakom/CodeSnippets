def test_st_plotly_chart_sharing(self):
        """Test st.plotly_chart when sending data to Plotly's service."""
        import plotly.graph_objs as go

        trace0 = go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17])

        data = [trace0]

        with patch(
            "streamlit.elements.plotly_chart." "_plot_to_url_or_load_cached_url"
        ) as plot_patch:
            plot_patch.return_value = "the_url"
            st.plotly_chart(data, sharing="public")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.plotly_chart.HasField("figure"), False)
        self.assertNotEqual(el.plotly_chart.url, "the_url")
        self.assertEqual(el.plotly_chart.use_container_width, False)