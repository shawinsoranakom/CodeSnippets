def test_to_dict_all_metadata_fields(self):
        """to_dict should include all enriched metadata fields."""
        node = XBRLNode(
            element_id="us-gaap_Revenue",
            label="Revenue",
            order=2.0,
            level=0,
            parent_id=None,
            documentation="Total revenue recognized.",
            xbrl_type="monetaryItemType",
            period_type="duration",
            balance_type="credit",
            abstract=False,
            substitution_group="item",
            nillable=True,
            preferred_label="http://www.xbrl.org/2003/role/terseLabel",
        )
        d = node.to_dict()
        assert d["xbrl_type"] == "monetaryItemType"
        assert d["period_type"] == "duration"
        assert d["balance_type"] == "credit"
        assert d["substitution_group"] == "item"
        assert d["nillable"] is True
        assert d["preferred_label"] == "http://www.xbrl.org/2003/role/terseLabel"
        assert d["documentation"] == "Total revenue recognized."