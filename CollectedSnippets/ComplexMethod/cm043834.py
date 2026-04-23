def test_hmrc_dpl_frc_core_labels(self, hmrc_dpl_loaded):
        """FRC core labels should be loaded for cross-taxonomy resolution."""
        _, nodes = hmrc_dpl_loaded
        flat = _flatten_nodes(nodes)

        core_items = [f for f in flat if f["name"].startswith("core_")]
        assert len(core_items) > 0, "No FRC core elements found"

        labeled_core = [
            f for f in core_items if f.get("label") and f["label"] != f["name"]
        ]
        assert (
            len(labeled_core) > 0
        ), "FRC core labels not loaded — all core_* elements still show element_id as label"