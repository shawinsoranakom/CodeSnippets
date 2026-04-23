def test_plotly(self):
        import plotly.graph_objs as go

        """Test st.write with plotly object."""
        with patch("streamlit.delta_generator.DeltaGenerator.plotly_chart") as p:
            st.write([go.Scatter(x=[1, 2], y=[10, 20])])

            p.assert_called_once()