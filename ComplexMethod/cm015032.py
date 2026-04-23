def test_cow_input(self, device, dtype, op):
        samples = op.sample_inputs(device, dtype, requires_grad=op.supports_autograd)

        def is_strided_tensor(arg):
            return torch.is_tensor(arg) and arg.layout == torch.strided

        def check_ignore_materialize(idx_or_kw, allow_list):
            return (allow_list is not None) and (idx_or_kw in allow_list)

        def check_cow_input(
            arg,
            arg_copy,
            arg_raw,
            idx_or_kw,
            backward_or_forward="forward",
            supports_cow_input_no_materialize=op.supports_cow_input_no_materialize_forward,
            allow_list=op.allow_cow_input_materialize_forward,
        ):
            arg_name = (
                f"Argument {idx_or_kw}"
                if isinstance(idx_or_kw, int)
                else f"Keyword argument '{idx_or_kw}'"
            ) + f" during {backward_or_forward} call"

            if is_strided_tensor(arg):
                self.assertTrue(
                    torch._C._is_cow_tensor(arg_raw),
                    msg=(
                        f"{arg_name} raw input should remain COW, but it "
                        "unexpectedly materialized."
                    ),
                )
                is_cow = torch._C._is_cow_tensor(arg)

                if supports_cow_input_no_materialize and not check_ignore_materialize(
                    idx_or_kw, allow_list
                ):
                    self.assertTrue(
                        is_cow,
                        msg=(
                            f"{arg_name} unexpectedly materializes. "
                            f"Either set `supports_cow_input_no_materialize_{backward_or_forward}=False` "
                            "in this operation's OpInfo, add the arg to the OpInfo's "
                            f"`allow_cow_input_materialize_{backward_or_forward}` list, or change the "
                            "implementation to avoid materialization."
                        ),
                    )

                if is_cow:
                    self.assertTrue(
                        torch.allclose(arg, arg_copy, rtol=0, atol=0, equal_nan=True),
                        msg=(
                            f"{arg_name} avoided materialization, "
                            "but the operation mutated its data."
                        ),
                    )
                else:
                    self.assertTrue(
                        torch.allclose(
                            arg_raw, arg_copy, rtol=0, atol=0, equal_nan=True
                        ),
                        msg=(
                            f"{arg_name} materialized, which is allowed in this "
                            "case, but the COW input data was mutated, which is "
                            "not allowed."
                        ),
                    )

        for sample in samples:
            args_raw = [sample.input] + list(sample.args)
            kwargs_raw = sample.kwargs
            args_copy = []
            args = []
            kwargs_copy = {}
            kwargs = {}

            # Convert strided tensor inputs to COW tensors and make copies of
            # all inputs
            for arg in args_raw:
                if is_strided_tensor(arg):
                    args_copy.append(arg.detach().clone())
                    args.append(torch._lazy_clone(arg))
                else:
                    if torch.is_tensor(arg):
                        args_copy.append(arg.detach().clone())
                    else:
                        args_copy.append(copy.deepcopy(arg))
                    args.append(arg)

            for kw, arg in kwargs_raw.items():
                if is_strided_tensor(arg):
                    kwargs_copy[kw] = arg.detach().clone()
                    kwargs[kw] = torch._lazy_clone(arg)
                else:
                    if torch.is_tensor(arg):
                        kwargs_copy[kw] = arg.detach().clone()
                    else:
                        kwargs_copy[kw] = copy.deepcopy(arg)
                    kwargs[kw] = arg

            leaf_tensors = composite_compliance.gather_leaf_tensors(args, kwargs)

            # Call forward op
            results_raw = op.get_op()(*args, **kwargs)

            # Check that COW inputs remain COW after the forward op is executed
            for idx, arg in enumerate(args):
                check_cow_input(arg, args_copy[idx], args_raw[idx], idx)

            for kw, arg in kwargs.items():
                check_cow_input(arg, kwargs_copy[kw], kwargs_raw[kw], kw)

            # Call backward op if it is supported. This part of the test is
            # based on `composite_compliance.check_backward_formula`
            if (
                op.supports_autograd
                and len(leaf_tensors) > 0
                and not op.skip_cow_input_backward
            ):
                if sample.output_process_fn_grad is not None:
                    results_raw = sample.output_process_fn_grad(results_raw)

                leaf_results = pytree.tree_leaves(results_raw)
                results = [
                    r
                    for r in leaf_results
                    if isinstance(r, torch.Tensor) and r.requires_grad
                ]

                all_results_strided = all(
                    is_strided_tensor(result) for result in results
                )

                # Only test backward if the results are strided tensors
                if all_results_strided:
                    output_grads_raw = [
                        torch.ones(r.shape, device=r.device, dtype=r.dtype)
                        for r in results
                    ]
                    output_grads_copy = []
                    output_grads = []

                    # Convert output grads to COW tensors and make copies
                    for output_grad in output_grads_raw:
                        output_grads_copy.append(output_grad.detach().clone())
                        output_grads.append(torch._lazy_clone(output_grad))

                    torch.autograd.grad(
                        results,
                        leaf_tensors,
                        output_grads,
                        allow_unused=True,
                        retain_graph=True,
                    )

                    # Check that COW inputs remain COW after the backward op is executed
                    for idx, arg in enumerate(args):
                        check_cow_input(
                            arg,
                            args_copy[idx],
                            args_raw[idx],
                            idx,
                            backward_or_forward="backward",
                            supports_cow_input_no_materialize=op.supports_cow_input_no_materialize_backward,
                            allow_list=op.allow_cow_input_materialize_backward,
                        )

                    # Check that COW inputs remain COW after the backward op is executed
                    for idx, output_grad in enumerate(output_grads):
                        check_cow_input(
                            output_grad,
                            output_grads_copy[idx],
                            output_grads_raw[idx],
                            f"output grad {idx}",
                            backward_or_forward="backward",
                            supports_cow_input_no_materialize=op.supports_cow_input_no_materialize_backward,
                            allow_list=op.allow_cow_input_materialize_backward,
                        )