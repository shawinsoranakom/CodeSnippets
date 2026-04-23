def test_bop_credit_debit_resolves_under_net_parent(self, mock_bop_dependencies):
        """Credit and Debit rows must resolve under the hierarchy's Net parent."""
        from openbb_imf.utils.table_builder import ImfTableBuilder

        builder = ImfTableBuilder()
        result = builder.get_table("BOP", "H_BOP_FAKE", COUNTRY="AU")

        rows = [r for r in result["data"] if r.get("INDICATOR_code") == "SINCEX"]
        # Expect both Credit and Debit to be kept (not dropped)
        assert len(rows) == 2

        for row in rows:
            # Composite match should use hierarchy parent (NETCD_T), not CD_T/DB_T
            assert row.get("parent_code") == "NETCD_T"
            assert "excluding exceptional financing" in (row.get("title") or "")

        titles = {r.get("title") for r in rows}
        assert any(t and t.endswith(", Credit") for t in titles)
        assert any(t and t.endswith(", Debit") for t in titles)