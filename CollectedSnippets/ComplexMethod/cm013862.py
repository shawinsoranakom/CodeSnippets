def _maybe_emit_sync_dealloc(self, var: TensorVariable) -> None:
        from .variables.streams import get_current_stream, new_event

        device = var.device
        if device is None or device.type not in ("cuda", "xpu"):
            return

        node = var.proxy.node
        alloc_stream = node.meta.get("custom", {}).get("stream", None)

        users = set(node.users.keys())
        if not users:
            return
        last_user = None
        for n in self.output.graph.nodes:
            if n in users:
                last_user = n
        if last_user is None or last_user.op == "output":
            return

        last_use_stream = last_user.meta.get("custom", {}).get("stream", None)
        if alloc_stream == last_use_stream:
            return

        if alloc_stream is None:
            alloc_stream = get_current_stream(device)
        if last_use_stream is None:
            last_use_stream = get_current_stream(device)

        event_idx = new_event()
        self.output.create_proxy(
            "call_function",
            torch.ops.streams.record_event,
            (event_idx, last_use_stream),
            {},
        )
        self.output.create_proxy(
            "call_function",
            torch.ops.streams.sync_dealloc,
            (event_idx, alloc_stream, var.as_proxy()),
            {},
        )