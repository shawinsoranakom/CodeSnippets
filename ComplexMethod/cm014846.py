def collect_frames(
        self, augmented_snapshot, collect_device_traces=True, collect_segments=True
    ):
        """Collects all frames that has node metadata from a memory snapshot."""
        # Collect all frames with FX metadata
        fx_frames = []

        # Check device traces for FX debug fields
        if collect_device_traces:
            for trace_list in augmented_snapshot.get("device_traces", []):
                for trace_entry in trace_list:
                    if not isinstance(trace_entry, dict):
                        continue
                    for frame in trace_entry.get("frames", []):
                        if not isinstance(frame, dict):
                            continue
                        if "fx_node_op" in frame or "fx_node_name" in frame:
                            fx_frames.append(frame)

        # Check segments/blocks for FX debug fields
        if collect_segments:
            for segment in augmented_snapshot.get("segments", []):
                for block in segment.get("blocks", []):
                    for frame in block.get("frames", []):
                        if not isinstance(frame, dict):
                            continue
                        if "fx_node_op" in frame or "fx_node_name" in frame:
                            fx_frames.append(frame)
        return fx_frames