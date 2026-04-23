def _sample_rightmost_arg(
        self,
        opinfo,
        rightmost_arg_type,
        device,
        dtype,
        num_tensors,
        allow_higher_dtype_scalars,
        **_foreach_inputs_kwargs,
    ):
        if rightmost_arg_type == ForeachRightmostArgType.TensorList:
            return [sample_inputs_foreach(None, device, dtype, num_tensors, **_foreach_inputs_kwargs)]
        if rightmost_arg_type == ForeachRightmostArgType.Tensor:
            return [make_tensor(
                (), device=device, dtype=dtype,
                noncontiguous=_foreach_inputs_kwargs["noncontiguous"],
                requires_grad=_foreach_inputs_kwargs.get("requires_grad", False),
            )]
        should_use_simpler_scalars = opinfo.name == "_foreach_pow" and dtype in (torch.float16, torch.bfloat16)

        def sample_float():
            s = random.random()
            if should_use_simpler_scalars:
                return 1.0 if s > 0.5 else 2.0
            else:
                return 1.0 - s

        high = 2 if should_use_simpler_scalars else 9
        if rightmost_arg_type == ForeachRightmostArgType.ScalarList:
            scalarlist_list = []
            scalarlist_list.append([random.randint(0, high) + 1 for _ in range(num_tensors)])

            if allow_higher_dtype_scalars or dtype.is_floating_point:
                scalarlist_list.append([sample_float() for _ in range(num_tensors)])
            if allow_higher_dtype_scalars or dtype.is_complex:
                scalarlist_list.append([complex(sample_float(), sample_float()) for _ in range(num_tensors)])
                scalarlist_list.append([1, 2.0, 3.0 + 4.5j] + [3.0 for _ in range(num_tensors - 3)])
                scalarlist_list.append([True, 1, 2.0, 3.0 + 4.5j] + [3.0 for _ in range(num_tensors - 4)])
            return scalarlist_list
        if rightmost_arg_type == ForeachRightmostArgType.Scalar:
            scalars = []
            scalars.append(random.randint(1, high + 1))
            if allow_higher_dtype_scalars or dtype.is_floating_point:
                scalars.append(sample_float())
            if allow_higher_dtype_scalars or dtype.is_complex:
                scalars.append(complex(sample_float(), sample_float()))
            scalars.append(True)
            return scalars
        raise AssertionError(f"Invalid rightmost_arg_type of {rightmost_arg_type}")