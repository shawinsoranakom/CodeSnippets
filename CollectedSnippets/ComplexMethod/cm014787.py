def collect_frames(
        self, augmented_snapshot, collect_device_traces=True, collect_segments=True
    ):
        """Collects all frames that has node metadata from a memory snapshot."""
        # Collect all frames with FX metadata
        fx_frames = []

        # Check device traces for FX debug fields
        if collect_device_traces and "device_traces" in augmented_snapshot:
            for trace_list in augmented_snapshot["device_traces"]:
                for trace_entry in trace_list:
                    if isinstance(trace_entry, dict) and "frames" in trace_entry:
                        for frame in trace_entry["frames"]:
                            if isinstance(frame, dict):
                                # Check for FX debug fields
                                if "fx_node_op" in frame or "fx_node_name" in frame:
                                    fx_frames.append(frame)

        # Check segments/blocks for FX debug fields
        if collect_segments and "segments" in augmented_snapshot:
            for segment in augmented_snapshot["segments"]:
                if "blocks" in segment:
                    for block in segment["blocks"]:
                        if "frames" in block:
                            for frame in block["frames"]:
                                if isinstance(frame, dict):
                                    if "fx_node_op" in frame or "fx_node_name" in frame:
                                        fx_frames.append(frame)
        return fx_frames