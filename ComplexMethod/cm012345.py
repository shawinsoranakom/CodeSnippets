def __call__(self, graph: torch.fx.Graph):
        for node in graph.nodes:
            if node.op != "call_function":
                continue
            if isinstance(node.target, (OpOverload, OpOverloadPacket)):
                # only applies to torch ops; e.g. torch.stack(axis=1) works, torch.ops.aten.stack(axis=1) doesn't.
                continue
            kwargs = node.kwargs

            if node.target in self.cache:
                replaceable_kwargs = self.cache[node.target]
            else:
                signatures = torch.fx.operator_schemas.get_signature_for_torch_op(
                    node.target
                )
                signatures = () if signatures is None else signatures
                replaceable_kwargs = OrderedSet()
                for sig in signatures:
                    for param_name in sig.parameters:
                        if param_name in self.numpy_compat:
                            replaceable_kwargs.update(self.numpy_compat[param_name])

                self.cache[node.target] = replaceable_kwargs

            if not replaceable_kwargs:
                continue

            new_kwargs = {}
            kwargs_changed = False
            for k, v in kwargs.items():
                if k in replaceable_kwargs:
                    kwargs_changed = True
                    new_kwargs[self.inverse_mapping[k]] = v
                else:
                    new_kwargs[k] = v

            if kwargs_changed:
                node.kwargs = torch.fx.immutable_collections.immutable_dict(new_kwargs)
                counters["inductor"]["numpy_compat_normalization"] += 1