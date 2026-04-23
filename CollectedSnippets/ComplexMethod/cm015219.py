def test():
            # Error inputs check
            if op.error_inputs_func is not None:
                error_inputs = op.error_inputs(device)
                for error_input in error_inputs:
                    sample_input = error_input.sample_input
                    args = (sample_input.input,) + tuple(sample_input.args)
                    kwargs = sample_input.kwargs
                    for batched_args, in_dims, _ in generate_vmap_inputs(args, {}):
                        with self.assertRaises(Exception):
                            vmap(op, in_dims)(*batched_args, **kwargs)

            # Sample inputs check
            sample_inputs_op = {
                # Take too long with reference inputs
                "special.chebyshev_polynomial_t",
                "special.chebyshev_polynomial_u",
                "special.chebyshev_polynomial_v",
                "special.chebyshev_polynomial_w",
                "special.hermite_polynomial_he",
                "special.laguerre_polynomial_l",
                "special.legendre_polynomial_p",
                "special.shifted_chebyshev_polynomial_t",
                "special.shifted_chebyshev_polynomial_u",
                "special.shifted_chebyshev_polynomial_v",
                "special.shifted_chebyshev_polynomial_w",
            }
            if op.name in sample_inputs_op:
                sample_inputs_itr = op.sample_inputs(
                    device, dtype, requires_grad=False, use_subtests=True
                )
            else:
                sample_inputs_itr = op.reference_inputs(
                    device, dtype, requires_grad=False, use_subtests=True
                )
            aliases, inplace_aliases = discover_variants(op)
            check_shape_only = op.name in ("empty_like", "new_empty")
            for sample_input, subtest_ctx, skip_xfail_ctx in sample_inputs_itr:
                with subtest_ctx(self), skip_xfail_ctx(self):
                    args = (sample_input.input,) + sample_input.args
                    if not any(isinstance(arg, torch.Tensor) for arg in args):
                        # At least one tensor required for vmap.
                        continue
                    kwargs = sample_input.kwargs
                    is_batch_norm_and_training = is_batch_norm_training(op.name, kwargs)
                    out_dim = 0
                    if op.name == "NumpySplitCopyWithIntCustomOp":
                        # special case for this custom op
                        def sample_vmap_out_dim_numpy_split_copy_with_int(
                            x, splits, dim
                        ):
                            return [0 for _ in range(len(splits) + 1)], None

                        out_dim = sample_vmap_out_dim_numpy_split_copy_with_int(*args)
                    for batched_args, in_dims, _ in generate_vmap_inputs(
                        args, {}, is_batch_norm_and_training=is_batch_norm_and_training
                    ):
                        for func in aliases:
                            self.vmap_outplace_test(
                                func,
                                batched_args,
                                kwargs,
                                in_dims,
                                check_shape_only,
                                postprocess_fn,
                                out_dim=out_dim,
                            )
                        if op.name in skip_inplace:
                            continue
                        if not is_valid_inplace_sample_input(
                            sample_input, op, op.inplace_variant
                        ):
                            continue
                        for func in inplace_aliases:
                            self.vmap_inplace_test(
                                func, batched_args, kwargs, in_dims, postprocess_fn
                            )