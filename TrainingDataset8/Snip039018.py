def test_basic(self):
        """Test that plotly object works."""
        df = px.data.gapminder().query("country=='Canada'")
        fig = px.line(df, x="year", y="lifeExp", title="Life expectancy in Canada")
        st.plotly_chart(fig)

        el = self.get_delta_from_queue().new_element
        self.assertNotEqual(el.plotly_chart.figure.spec, None)
        self.assertNotEqual(el.plotly_chart.figure.config, None)