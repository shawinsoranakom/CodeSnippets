def test_returns_categories_with_subcategories(self):
        """Return categories with their subcategories and tool counts."""
        index = CategoryIndex()
        index.register(
            category="equity", subcategory="price", tool_name="equity_price_historical"
        )
        index.register(
            category="equity",
            subcategory="fundamental",
            tool_name="equity_fundamental_income",
        )
        index.register(
            category="economy", subcategory="general", tool_name="economy_cpi"
        )

        settings = MCPSettings(enable_tool_discovery=True)  # type: ignore
        _, decorated, _ = _build_server(settings, index=index)

        result = decorated["available_categories"]()
        names = {c.name for c in result}
        assert names == {"equity", "economy"}

        equity = next(c for c in result if c.name == "equity")
        assert equity.total_tools == 2
        subcat_names = {s.name for s in equity.subcategories}
        assert subcat_names == {"price", "fundamental"}