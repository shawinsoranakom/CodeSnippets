def _rerun_node_after_type_promotion(
        self,
        node: torch.fx.Node,
        expected_out_dtype: torch.dtype,
    ) -> None:
        """Rerun a node after type promotion and update node.meta["val"] with the output value."""
        node_val = node.meta.get("val", None)
        if node_val is None:
            raise AssertionError(f"Node {node} node.meta['val'] is not set.")
        args, kwargs = self.fetch_args_kwargs_from_env(node)
        target = node.target
        if not isinstance(target, torch._ops.OpOverload):
            raise AssertionError(f"Expected OpOverload, got {type(target)}")
        node.target = find_compatible_op_overload(target.overloadpacket, args, kwargs)

        new_node_val = self._run_node_and_set_meta(node)
        if not isinstance(new_node_val, type(node_val)):
            raise AssertionError(
                f"run_node output type should not change between runs. "
                f"Got {type(new_node_val)}, expect {type(node_val)}."
            )

        if isinstance(node_val, torch.Tensor):
            prev_node_dtype = node_val.dtype

            if prev_node_dtype != expected_out_dtype:
                raise AssertionError(
                    f"node.meta['val'].dtype({prev_node_dtype}) does not agree with "
                    f"type promotion rule({expected_out_dtype})."
                )

            if new_node_val.dtype != expected_out_dtype:
                # With explicit type promotion, the expected result dtype may not be
                # the same as the computation dtype. This is referred to as "op math".
                # We need to explicitly cast the output back to the expected dtype.
                # See more about "op math" topic at `_prims_common.elementwise_dtypes`.
                graph = node.graph
                with graph.inserting_after(node):
                    output_cast_node = self._create_node(
                        graph,
                        "call_function",
                        torch.ops.prims.convert_element_type.default,
                        (node,),
                        {"dtype": expected_out_dtype},
                    )
                    node.replace_all_uses_with(output_cast_node)
                    output_cast_node.args = (node,)
                    logger.info(
                        "Node '%s' output dtype becomes %s due to op math. "
                        "Cast back to %s.",
                        node,
                        new_node_val.dtype,
                        expected_out_dtype,
                    )

        elif fx_type_utils.is_torch_symbolic_type(node_val):
            raise NotImplementedError(
                "Type promotion does not support node output of sym types."
            )
        elif isinstance(node_val, (list, tuple)):
            raise NotImplementedError(
                "Type promotion does not support node output of list or tuple."
            )
        else:
            raise RuntimeError(f"Unexpected node output type: {type(node_val)}.")