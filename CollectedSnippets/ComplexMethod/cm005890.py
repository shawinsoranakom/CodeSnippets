def test_template_nodes_no_overlap(self, template_file):
        """Test that no two generic nodes overlap on the canvas."""
        with template_file.open(encoding="utf-8") as f:
            template_data = json.load(f)

        nodes = template_data.get("data", {}).get("nodes", [])

        # Collect bounding boxes for generic (non-note) nodes
        boxes = []
        for node in nodes:
            if node.get("type") == "noteNode":
                continue
            pos = node.get("position", {})
            measured = node.get("measured", {})
            x = pos.get("x")
            y = pos.get("y")
            w = measured.get("width")
            h = measured.get("height")
            if x is None or y is None or w is None or h is None:
                continue
            display = node.get("data", {}).get("display_name") or node.get("data", {}).get("type", node.get("id", "?"))
            boxes.append((display, x, y, w, h))

        # Minimum overlap in pixels on each axis to count as a real overlap.
        # Stored `measured` dimensions can be slightly stale, so ignore
        # near-miss intersections smaller than this threshold.
        min_overlap_px = 20

        errors = []
        for i, (name_a, ax, ay, aw, ah) in enumerate(boxes):
            for name_b, bx, by, bw, bh in boxes[i + 1 :]:
                # Compute overlap extent on each axis
                overlap_x = min(ax + aw, bx + bw) - max(ax, bx)
                overlap_y = min(ay + ah, by + bh) - max(ay, by)
                if overlap_x > min_overlap_px and overlap_y > min_overlap_px:
                    errors.append(f"  '{name_a}' and '{name_b}' overlap on the canvas")

        if errors:
            error_msg = "\n".join(errors)
            pytest.fail(f"Node overlaps in {template_file.name}:\n{error_msg}")