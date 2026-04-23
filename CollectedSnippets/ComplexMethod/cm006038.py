def format_state_deltas(self) -> str:
        """Format state deltas as human-readable text.

        Returns:
            Formatted string showing what changed at each step
        """
        lines = ["\n=== STATE DELTAS ===\n"]

        for delta in self.state_deltas:
            vertex_id = delta.get("vertex_id", "Unknown")
            step = delta.get("step", "?")

            lines.append(f"Step {step}: {vertex_id}")

            # Show run_manager changes
            if "run_manager" in delta:
                rm_delta = delta["run_manager"]

                if "run_predecessors" in rm_delta:
                    lines.append("  run_predecessors:")
                    for vid, change in rm_delta["run_predecessors"].items():
                        if change["added"]:
                            lines.append(f"    {vid} += {change['added']}")
                        if change["removed"]:
                            lines.append(f"    {vid} -= {change['removed']}")

                if "run_map" in rm_delta:
                    lines.append("  run_map:")
                    for vid, change in rm_delta["run_map"].items():
                        if change["added"]:
                            lines.append(f"    {vid} += {change['added']}")
                        if change["removed"]:
                            lines.append(f"    {vid} -= {change['removed']}")

            # Show queue changes
            if "queue" in delta:
                q_delta = delta["queue"]
                if q_delta["added"]:
                    lines.append(f"  queue += {q_delta['added']}")
                if q_delta["removed"]:
                    lines.append(f"  queue -= {q_delta['removed']}")
                lines.append(f"  queue size: {q_delta['before_size']} → {q_delta['after_size']}")

            lines.append("")

        return "\n".join(lines)