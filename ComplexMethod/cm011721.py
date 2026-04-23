def _has_layout_conflict_for_template(
        self, multi_node: ir.MultiTemplateBuffer
    ) -> bool:
        """
        Check if selecting a Triton template would cause layout conflicts.
        Returns True if there's a conflict and we should fall back to ATen.
        """
        constraints = V.graph.buffer_layout_constraints
        if not constraints:
            return False

        log.debug("Node %s has constraints %s", multi_node, constraints)
        for inp in multi_node.inputs:
            # pyrefly: ignore [missing-attribute]
            inp_name = inp.get_name()
            # View has its own fixed layout that is not constrained
            if (
                not getattr(inp, "layout", None)
                or inp_name not in constraints
                or isinstance(inp, ir.ReinterpretView)
            ):
                continue

            layout = inp.layout
            expected_layout = constraints[inp_name]
            if isinstance(layout, ir.FlexibleLayout):
                # Freeze to the expected layout to avoid conflicts
                # pyrefly: ignore [missing-attribute]
                inp.freeze_layout_with_exact_strides(expected_layout.stride)
                layout = inp.layout

            if isinstance(layout, ir.FixedLayout) and expected_layout != layout:
                # Layout already frozen to a different layout - conflict
                log.warning(
                    "Layout conflict detected for %s: template expects %s but layout is frozen to %s",
                    inp_name,
                    expected_layout,
                    layout,
                )
                return True

        return False