def create_node(self, *args: object, **kwargs: object) -> fx.node.Node:
        """
        Create node and add on metadata.
        Add nn_module_stack here instead of TracerBase,
        since calls to make_fx() might not want to record module stack metadata.
        Add torch_fn by looking at torch_fn_metadata and torch_fn_counts.
        Add stack_trace by filtering out forward() stack frames.
        """
        node = super().create_node(*args, **kwargs)  # type: ignore[arg-type]

        # nn_module_stack
        if node.op not in ["placeholder", "output"]:
            if node.meta.get("nn_module_stack") is None:
                node.meta["nn_module_stack"] = self.module_stack.copy()
            # convert nn_module_stack from Dict[key, (FQN, class)] -> Dict[str, Tuple[str, str]]
            for key, (fqn, mod_cls) in node.meta["nn_module_stack"].items():
                if isinstance(mod_cls, type):
                    node.meta["nn_module_stack"][key] = (
                        fqn,
                        mod_cls.__module__ + "." + mod_cls.__qualname__,
                    )

        # torch_fn
        if (
            node.op == "call_function"
            and (torch_fn := self.torch_fn_metadata) is not None
            and "torch_fn" not in node.meta
        ):
            node.meta["torch_fn"] = (
                # pyrefly: ignore[missing-attribute,bad-index]
                f"{torch_fn.__name__}_{self.torch_fn_counts[torch_fn]}",
                # pyrefly: ignore[missing-attribute]
                f"{torch_fn.__class__.__name__}.{torch_fn.__name__}",
            )

        return node