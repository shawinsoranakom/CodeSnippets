def test_hmrc_dpl_structure(self, hmrc_dpl_loaded):
        """get_structure should return presentation tree for HMRC DPL."""
        _, nodes = hmrc_dpl_loaded
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        assert all(isinstance(n, XBRLNode) for n in nodes)

        flat = _flatten_nodes(nodes)
        element_ids = {f["name"] for f in flat}

        assert any(eid.startswith("dpl_") for eid in element_ids)
        assert any(eid.startswith("core_") for eid in element_ids)
        assert len(flat) >= 500, f"Expected >=500 items, got {len(flat)}"