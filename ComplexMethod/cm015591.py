def _test_op(op, *args, linearity=None, inplace=None):
            # Auto-detect inplace ops by checking for "_." in the op name (e.g., _foreach_add_.List)
            if inplace is None:
                inplace = "_." in str(op)

            # creates specs, computes single-dim strategy, and expands to mesh
            out_spec = None
            specs = []
            for arg in args:
                if isinstance(arg, list):
                    tensor_specs = []
                    for p, t in arg:
                        spec = DTensorSpec(
                            mesh,
                            p,
                            TensorMeta(t.shape, t.stride(), t.dtype),
                        )
                        tensor_specs.append(
                            OpStrategy([OpSpec(spec)]),
                        )
                    list_spec = TupleStrategy(tuple(tensor_specs))
                    if out_spec is None:
                        out_spec = list_spec
                    specs.append(list_spec)
                else:
                    specs.append(arg)

            output_meta = [spec.tensor_meta for spec in out_spec.children]

            op_schema = OpSchema(op=op, args_schema=tuple(specs), kwargs_schema={})
            extra_rules = _BINARY_ADDITIVE_RULES if linearity == 1 else None
            strategy_fn = _common_pointwise_single_dim_strategy(
                partial_extra_rules=extra_rules
            )
            expanded = _expand_single_dim_strategy_to_mesh(
                mesh, op_schema, _SingleDimStrategyInfo(strategy_fn), output_meta
            )
            strategy = expanded(op, op_schema.args_meta, op_schema.kwargs_meta)

            # check expanded strategy
            self.assertIsInstance(strategy, TupleStrategy)
            self.assertEqual(
                len(strategy.children), len(args[0])
            )  # no. of list elements
            if inplace:
                # For inplace ops, the self argument cannot be redistributed,
                # so there should be exactly 1 strategy (the input placement)
                self.assertEqual(len(strategy.children[0].strategies), 1)
            elif linearity == 1:
                # See test_expand_foreach_add_to_3d_mesh for derivation of 634.
                self.assertEqual(len(strategy.children[0].strategies), 634)
            else:
                self.assertGreaterAlmostEqual(
                    len(strategy.children[0].strategies), 64
                )