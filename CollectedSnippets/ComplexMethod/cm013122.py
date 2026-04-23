def _maybe_promote_arg(
        self,
        node: torch.fx.Node,
        fx_arg: torch.fx.node.Argument,
        dtype: torch.dtype | None,
    ) -> torch.fx.node.Argument:
        """Promote fx_arg to dtype if necessary."""
        if dtype is None:
            logger.info(
                "Argument %s is not promoted. Not mentioned by type promotion rule.",
                fx_arg,
            )
            return fx_arg

        if isinstance(fx_arg, torch.fx.Node):
            arg_val = self.env[fx_arg]
            if isinstance(arg_val, torch.Tensor):
                if (old_dtype := arg_val.dtype) != dtype:
                    # Promote tensor to dtype.
                    graph = node.graph
                    with graph.inserting_before(node):
                        logger.info(
                            "Argument %s(%s) is promoted to %s.",
                            fx_arg,
                            old_dtype,
                            dtype,
                        )
                        return self._create_node(
                            graph,
                            "call_function",
                            torch.ops.prims.convert_element_type.default,
                            (fx_arg,),
                            {"dtype": dtype},
                        )
                logger.info("Argument %s is not promoted. Already %s.", fx_arg, dtype)
                return fx_arg
            elif fx_type_utils.is_torch_symbolic_type(arg_val):
                arg_type = type(arg_val)
                equivalent_dtype = fx_type_utils.from_scalar_type_to_torch_dtype(
                    arg_type
                )
                if equivalent_dtype is None:
                    raise AssertionError(f"Unexpected arg_type: {arg_type}")
                if equivalent_dtype != dtype:
                    # Promote Sym number to tensor of dtype.
                    graph = node.graph
                    with graph.inserting_before(node):
                        logger.info(
                            "Argument %s(Scalar of equivalent dtype: %s) "
                            "is promoted to %s.",
                            fx_arg,
                            equivalent_dtype,
                            dtype,
                        )
                        return self._create_node(
                            graph,
                            "call_function",
                            torch.ops.aten.scalar_tensor.default,
                            (fx_arg,),
                            {"dtype": dtype},
                        )
                logger.info("Argument %s is not promoted. Already %s.", fx_arg, dtype)
                return fx_arg
        elif (
            equivalent_dtype := fx_type_utils.from_scalar_type_to_torch_dtype(
                type(fx_arg)
            )
        ) is not None:
            if equivalent_dtype != dtype:
                # Promote number to tensor of dtype.
                # The op should have overload that supports tensor for this arg, otherwise
                # the type promotion rule should not suggest promoting this arg.
                graph = node.graph
                with graph.inserting_before(node):
                    logger.info(
                        "Argument %s(Scalar of equivalent dtype: %s) "
                        "is promoted to %s.",
                        fx_arg,
                        equivalent_dtype,
                        dtype,
                    )
                    return self._create_node(
                        graph,
                        "call_function",
                        torch.ops.aten.scalar_tensor.default,
                        (fx_arg,),
                        {"dtype": dtype},
                    )
            logger.info("Argument %s is not promoted. Already %s.", fx_arg, dtype)
            return fx_arg
        elif isinstance(fx_arg, (tuple, list)):
            logger.info("Argument %s is a tuple/list. Promoting each element.", fx_arg)
            return type(fx_arg)(
                self._maybe_promote_arg(node, fx_arg_elem, dtype)
                for fx_arg_elem in fx_arg
            )

        raise NotImplementedError(f"Unknown fx arg type: {type(fx_arg)}")