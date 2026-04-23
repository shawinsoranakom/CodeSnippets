def _populate_stream_assignments(self) -> None:
        """Populate node_to_stream and buff_to_stream from IR node stream_idx.

        Reads the stream_idx field set on IR nodes during lowering to determine
        which stream each scheduler node should run on. This field is propagated
        from 'custom.stream' FX node metadata via IRNode.current_stream_idx().
        """
        from .stream_constants import DEFAULT_STREAM_IDX

        # Map user_object_index to stream index (1-indexed for side streams)
        user_obj_to_stream_idx: dict[int, int] = {}
        stream_idx_counter = itertools.count(1)  # 0 is reserved for default stream

        for node in self.nodes:
            stream_idx = DEFAULT_STREAM_IDX

            if node.node is not None:
                user_obj_idx = node.node.get_stream_idx()
                if user_obj_idx is not None:
                    if user_obj_idx not in user_obj_to_stream_idx:
                        new_stream_idx = next(stream_idx_counter)
                        user_obj_to_stream_idx[user_obj_idx] = new_stream_idx
                        self.stream_idx_to_user_obj_idx[new_stream_idx] = user_obj_idx
                    stream_idx = user_obj_to_stream_idx[user_obj_idx]

            self.node_to_stream[node] = stream_idx

            # Also populate buff_to_stream for all buffers produced by this node.
            # Mutation renames are resolved at lookup time via get_buf_stream.
            for buf in node.get_buffer_names():
                self.buff_to_stream[buf] = stream_idx

        # Propagate a device to device-less nodes (e.g. record_event,
        # wait_event) so they naturally enter the device guard in the
        # main codegen loop instead of requiring special-case handling.
        if any(s != DEFAULT_STREAM_IDX for s in self.node_to_stream.values()):
            device = next(
                (n.get_device() for n in self.nodes if n.get_device() is not None), None
            )
            if device is not None:
                for node in self.nodes:
                    ir_node = node.node
                    if (
                        node.get_device() is None
                        and isinstance(ir_node, ir.Buffer)
                        and isinstance(ir_node.layout, ir.NoneLayout)
                    ):
                        # pyrefly: ignore [bad-assignment]
                        ir_node.layout = ir.NoneLayout(device=device)

        # Check if we have any nodes on non-default streams
        self._multi_stream_nodes = any(
            stream_idx != DEFAULT_STREAM_IDX
            for stream_idx in self.node_to_stream.values()
        )