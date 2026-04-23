def placeholder(
        self, target: Target, args: tuple[Argument, ...], kwargs: dict[str, Any]
    ) -> Any:
        """Replace old placeholders with new flattened ones."""
        # Return the corresponding new placeholder
        if self.current_node in self.old_to_new_mapping:
            new_arg = self.old_to_new_mapping[self.current_node]

            # Copy over additional metadata from current node, but don't overwrite "val"
            for key in ["tensor_dict", "example_value", "unbacked_bindings"]:
                if key in self.current_node.meta:
                    new_arg.node.meta[key] = self.current_node.meta[key]

            # Only copy "val" if we don't already have a good one
            if "val" in self.current_node.meta and "val" not in new_arg.node.meta:
                new_arg.node.meta["val"] = self.current_node.meta["val"]

            return new_arg
        else:
            # Convert captured objects (e.g., opaque objects from closures) to
            # get_attr nodes
            placeholder_idx = self.placeholders.index(self.current_node)
            if placeholder_idx in self.graph_inputs:
                source = self.graph_inputs[placeholder_idx]
                if not isinstance(source, torch._dynamo.source.GetItemSource):
                    example_val = self.current_node.meta.get(
                        "val"
                    ) or self.current_node.meta.get("example_value")
                    if example_val is not None:
                        attr_name = f"_captured_{placeholder_idx}"
                        if isinstance(example_val, torch.Tensor):
                            self.module.register_buffer(attr_name, example_val)
                        else:
                            setattr(self.module, attr_name, example_val)
                        result = self.tracer.create_proxy("get_attr", attr_name, (), {})
                        result.node.meta = self.current_node.meta.copy()
                        result.node.meta["val"] = example_val
                        return result
            return super().placeholder(target, args, kwargs)