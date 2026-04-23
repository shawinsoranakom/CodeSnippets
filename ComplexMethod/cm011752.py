def _log_non_cudagraphable_node(self, node: BaseSchedulerNode) -> None:
        """Log details for a non-cudagraphable node."""
        reason = self.should_partition(node)
        if not reason:
            return

        node_name = node.get_name()
        fx_node = node.node.get_origin_node() if node.node is not None else None
        parts = [f"reason={reason}"]
        ir_type = type(node.node).__name__
        parts.append(f"ir={ir_type}")
        if fx_node is not None:
            fx_str = f"{fx_node.target}({', '.join(str(a) for a in fx_node.args)})"
            parts.append(f"fx={fx_str}")

        cudagraphs_log.debug("    %s: %s", node_name, ", ".join(parts))

        # Log full stack trace if available
        if fx_node is not None:
            stack_trace = fx_node.meta.get("stack_trace", None)
            if stack_trace:
                for line in stack_trace.strip().split("\n"):
                    cudagraphs_log.debug("         %s", line)