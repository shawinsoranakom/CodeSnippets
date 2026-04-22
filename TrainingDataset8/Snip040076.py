def test_st_arrow_altair_chart(self):
        """Test st._arrow_altair_chart."""
        import altair as alt

        df = pd.DataFrame(np.random.randn(3, 3), columns=["a", "b", "c"])

        c = (
            alt.Chart(df)
            .mark_circle()
            .encode(x="a", y="b", size="c", color="c")
            .interactive()
        )
        st._arrow_altair_chart(c)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        spec = json.loads(proto.spec)

        # Checking Vega-Lite is a lot of work so rather than doing that, we
        # just checked to see if the spec data name matches the dataset.
        self.assertEqual(spec.get("data").get("name"), proto.datasets[0].name)