def _get_atomic_add_buffers(self) -> OrderedSet[str]:
        buffers_store_as_atomic_add: OrderedSet[str] = OrderedSet()
        if isinstance(self._body, LoopBody):
            for node in self._body.get_nodes():
                if (
                    node.op == "call_method"
                    and node.target == "store"
                    and (
                        ("mode" in node.kwargs and node.kwargs["mode"] == "atomic_add")
                        or (len(node.args) == 5 and node.args[4] == "atomic_add")
                    )
                ):
                    buffers_store_as_atomic_add.add(
                        node.kwargs["name"]
                        if "name" in node.kwargs
                        else (node.args[1] if len(node.args) >= 2 else "")
                    )
        return buffers_store_as_atomic_add