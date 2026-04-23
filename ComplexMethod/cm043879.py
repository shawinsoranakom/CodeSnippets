def test_bop_assets_liabilities_remain_distinct_paths(self, mock_bop_dependencies):
        """Assets and Liabilities must remain separate hierarchy paths."""
        from openbb_imf.utils.table_builder import ImfTableBuilder

        builder = ImfTableBuilder()
        result = builder.get_table("BOP", "H_BOP_FAKE", COUNTRY="AU")

        rows = [r for r in result["data"] if r.get("INDICATOR_code") == "O"]
        assert len(rows) == 2

        parent_codes = {r.get("parent_code") for r in rows}
        assert parent_codes == {"A_P", "L_P"}

        titles = {r.get("title") for r in rows}
        assert any(t and t.endswith(", Assets") for t in titles)
        assert any(t and t.endswith(", Liabilities") for t in titles)