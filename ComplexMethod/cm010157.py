def convert_aten_to(self, node: torch._C.Node):
        target = get_op_overload(node)
        args, _kwargs = self.get_args_kwargs(node, target._schema)

        # special handle aten.to.dtype and aten.to.prim_dtype followed by inplace_mutation_op
        # coz aten.to + inplace_mutation_op pattern would trigger
        # "cannot mutate tensors with frozen storage" functionalization error.
        # To work around the issue, we override the copy to be True, so that the output
        # is for sure not an alias of input
        if target is torch.ops.aten.to.dtype or target is torch.ops.aten.to.prim_dtype:
            user_nodes = [use.user for use in node.output().uses()]
            user_targets = [
                get_op_overload(user_node)
                for user_node in user_nodes
                if user_node.schema() != "(no schema)"
            ]
            has_mutable_target = any(
                target._schema.is_mutable for target in user_targets
            )

            if has_mutable_target:
                if len(args) < 4:
                    raise AssertionError(f"expected at least 4 args, got {len(args)}")
                new_args = list(args)
                new_args[3] = True  # copy, override to True
                fx_node = self.fx_graph.call_function(
                    torch.ops.aten.to.dtype, tuple(new_args)
                )
                # temp hack to work around the issue https://github.com/pytorch/pytorch/issues/131679
                # When this issue is fixed, the clone node would be no longer needed
                clone_node = self.fx_graph.call_function(
                    torch.ops.aten.clone.default, (fx_node,)
                )
                output_name = node.output().debugName()
                self.name_to_node[output_name] = clone_node
                return

        self.convert_call_function_op(node)