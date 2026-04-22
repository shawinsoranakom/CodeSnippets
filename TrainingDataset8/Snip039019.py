def test_theme(self, theme_value, proto_value):
        df = px.data.gapminder().query("country=='Canada'")
        fig = px.line(df, x="year", y="lifeExp", title="Life expectancy in Canada")
        st.plotly_chart(fig, theme=theme_value)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.plotly_chart.theme, proto_value)