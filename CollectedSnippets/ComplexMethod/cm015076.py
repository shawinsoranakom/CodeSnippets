def test_pointwise_op_with_tensor_of_scalarlist_overload(
        self, device, dtype, op, is_fastpath
    ):
        for sample in op.sample_inputs(
            device,
            dtype,
            noncontiguous=not is_fastpath,
            allow_higher_dtype_scalars=True,
        ):
            if not isinstance(sample.args, tuple):
                raise AssertionError(
                    f"expected sample.args to be tuple, got {type(sample.args)}"
                )
            if len(sample.args) != 2:
                raise AssertionError(
                    f"expected len(sample.args) == 2, got {len(sample.args)}"
                )
            inputs = [sample.input, *sample.args]
            kwargs = sample.kwargs.copy()
            disable_fastpath = sample.disable_fastpath and is_fastpath
            wrapped_op, ref, inplace_op, inplace_ref = self._get_funcs(op)
            scalars = kwargs.pop("scalars", None)

            if is_fastpath and scalars:
                sample = sample.transform(
                    lambda t: t.detach().clone() if torch.is_tensor(t) else t
                )
                inputs = [sample.input, *sample.args]
                tensor_values = torch.tensor(scalars)
                # 1D Tensor of scalars
                for is_inplace, op_, ref_ in (
                    (False, wrapped_op, ref),
                    (True, inplace_op, inplace_ref),
                ):
                    self._pointwise_test(
                        op_,
                        ref_,
                        inputs,
                        is_fastpath and not disable_fastpath,
                        is_inplace,
                        scalars=tensor_values,
                        **kwargs,
                    )
                    self._pointwise_test(
                        op_,
                        ref_,
                        inputs,
                        is_fastpath and not disable_fastpath,
                        is_inplace,
                        scalars=tensor_values[0],
                        custom_values_err="Expected packed scalar Tensor to be of dimension 1. Got 0 instead.",
                        **kwargs,
                    )
                    if self.is_cuda:
                        self._pointwise_test(
                            op_,
                            ref_,
                            inputs,
                            is_fastpath and not disable_fastpath,
                            is_inplace,
                            scalars=tensor_values.cuda(),
                            custom_values_err="Expected scalars to be on CPU, got cuda:0 instead.",
                            **kwargs,
                        )
                    self._pointwise_test(
                        op_,
                        ref_,
                        inputs,
                        is_fastpath and not disable_fastpath,
                        is_inplace,
                        scalars=tensor_values[:2],
                        custom_values_err=f"Expected length of scalars to match input of length {len(scalars)} but got 2 instead.",
                        **kwargs,
                    )
                    self._pointwise_test(
                        op_,
                        ref_,
                        inputs,
                        is_fastpath and not disable_fastpath,
                        is_inplace,
                        scalars=torch.tensor([[0, 1], [2, 3]])[:, 1],
                        custom_values_err="Expected scalars to be contiguous.",
                        **kwargs,
                    )

            # Tests of implicit broadcasting
            N = len(sample.input)
            inputs = [
                [
                    make_tensor(
                        (N, N),
                        device=device,
                        dtype=dtype,
                        noncontiguous=not is_fastpath,
                    )
                    for _ in range(N)
                ],
                [
                    make_tensor(
                        (N - i, 1),
                        device=device,
                        dtype=dtype,
                        noncontiguous=not is_fastpath,
                    )
                    for i in range(N)
                ],
                [
                    make_tensor(
                        (1, N - i),
                        device=device,
                        dtype=dtype,
                        noncontiguous=not is_fastpath,
                    )
                    for i in range(N)
                ],
            ]
            self._pointwise_test(
                wrapped_op,
                ref,
                inputs,
                is_fastpath and disable_fastpath,
                is_inplace=False,
                scalars=scalars,
                **kwargs,
            )
            self._pointwise_test(
                inplace_op,
                inplace_ref,
                inputs,
                is_fastpath and disable_fastpath,
                is_inplace=True,
                scalars=scalars,
                **kwargs,
            )