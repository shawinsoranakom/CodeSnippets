def extract_pw_from_reduction(self):
        red = None
        store = None
        for node in self.graph.nodes:
            if node.target == "reduction":
                assert not red
                red = node
            if node.target == "store_reduction":
                assert not store
                store = node
        assert red
        assert store
        reduction_type = red.args[-2]
        red_arg = red.args[-1]
        buf = store.args[1]
        ops = store.args[0]

        extra_meta = {
            "num_reduction_dims": len(self.body.reduce_vars),
        }
        with self.graph.inserting_after(store):
            self.graph.call_method(
                "partial_accumulate", (ops, buf, reduction_type, red_arg, extra_meta)
            )
        self.graph.erase_node(store)
        self.graph.erase_node(red)
        return self