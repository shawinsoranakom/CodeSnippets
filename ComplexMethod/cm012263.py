def _deduce_value(self, node: torch.fx.Node):
        # deduce value for full-like nodes
        # 1. for constructors, substitute value is a tensor of size [1]
        # 2. for view ops/indexing, substitute value is the same as the input
        # 3. for pointwise ops, run node to get the substitute value
        # 4. deal with some special ops
        # otherwise, stop deduce value and return unknown value

        # TODO: cat, more indexing
        # TODO - do on cpu to avoid syncs

        # single-elem attrs
        if node.op == "get_attr" or (
            node.op == "call_function"
            and node.target is torch.ops.aten.lift_fresh_copy.default
        ):
            out = super(ConstantFolder, self).run_node(node)
            if isinstance(out, torch.Tensor) and out.numel() == 1:
                return out

        # handle device_put op
        if node.target == prims.device_put.default:
            return super(ConstantFolder, self).run_node(node)

        # constructors ops
        if (
            node.op == "call_function"
            and node.target is aten.full.default
            and len(node.args) == 2
        ):
            args, kwargs = self.fetch_args_kwargs_from_env(node)
            value = args[1]
            # Don't specialize symbolic value.
            if not isinstance(value, (torch.SymInt, torch.SymFloat, torch.SymBool)):
                new_args = [[1], value]
                return aten.full.default(*new_args, **node.kwargs)

        # handle before view ops because this changes value
        if node.target is aten.view.dtype:
            (input_tensor, output_dtype), kwargs = self.fetch_args_kwargs_from_env(node)
            # view.dtype with different element sizes changes element count
            # (e.g., complex64 [1+0j] viewed as float32 becomes [1.0, 0.0]),
            # making uniform values non-uniform. Also crashes on 0-d tensors.
            if input_tensor.element_size() != output_dtype.itemsize:
                return self.unknown_value
            return super(ConstantFolder, self).run_node(node)

        # view ops, return input tensor, the first argument
        if hasattr(node.target, "overloadpacket") and (
            node.target.overloadpacket in self.view_op_packets
            or node.target.overloadpacket in self.indexing_op_packets
        ):
            assert isinstance(node.args[0], torch.fx.Node)
            return self.env[node.args[0]]

        # we don't want to return unknown value for symints so that we can
        # still constant fold through their use in constructors or views
        # if we see them in a pointwise node (e.g., tensor * symint)
        # we will bail
        if "val" in node.meta and isinstance(node.meta["val"], torch.SymInt):
            return node.meta["val"]

        # pointwise ops
        if isinstance(node.target, torch._ops.OpOverload) and (
            torch.Tag.pointwise in node.target.tags
            or node.target is torch.ops.aten.scalar_tensor.default
        ):
            args, kwargs = self.fetch_args_kwargs_from_env(node)
            flattened_inputs = pytree.arg_tree_leaves(*args, **kwargs)

            if any(isinstance(inp, torch.SymInt) for inp in flattened_inputs):
                return self.unknown_value

            # we run the ops with dim 1, so remove memory_format to avoid error
            kwargs = dict(kwargs)
            kwargs.pop("memory_format", None)

            return node.target(*args, **kwargs)

        return self.unknown_value