def inner(*inputs: TensorBox, alpha=None):
        if triton_fallback is not None and any(
            isinstance(inp, IRNode) and is_triton(inp) for inp in inputs
        ):
            assert not allow_alpha  # not implemented
            return triton_fallback(*inputs)

        inputs = promote_constants(inputs, override_return_dtype)
        if allow_alpha:
            if alpha is not None and alpha != 1:
                # Use FMA for add-with-alpha on CUDA floating-point.
                # Eager CUDA computes a + alpha * b as fma(b, alpha, a).
                if use_fma_for_alpha and isinstance(inputs[0], IRNode):
                    inp_device = inputs[0].get_device()
                    if (
                        inputs[0].get_dtype().is_floating_point
                        and not torch.version.hip
                        and inp_device is not None
                        and inp_device.type == "cuda"
                    ):
                        return _add_with_alpha_fma(inputs[0], inputs[1], alpha)

                # pyrefly: ignore [bad-assignment]
                inputs = list(inputs)
                # pyrefly: ignore [unsupported-operation]
                inputs[-1] = mul(inputs[-1], alpha)
        else:
            assert alpha is None
        loaders = [x.make_loader() for x in inputs]
        ranges = inputs[0].get_size()
        dtype = override_return_dtype or inputs[0].get_dtype()

        for other in inputs[1:]:
            assert isinstance(other, ir.BaseConstant) or len(ranges) == len(
                other.get_size()
            ), f"ndim mismatch {fn} {ranges} {other.get_size()}"

        # in tracing, we will annotate pointwise nodes that correspond to the output of
        # a pointwise node that would have been run in eager. intermediary pointwise nodes
        # during decompositions are not annotated.
        low_pr_fp = (torch.bfloat16, torch.float16)
        emulate_precision_casts = (
            V.graph is not None
            and getattr(V.graph, "current_node", None) is not None
            and V.graph.current_node.meta is not None
            and V.graph.current_node.meta.get("low_precision_pointwise_barrier", False)
        )
        emulate_output_cast = emulate_precision_casts and dtype in low_pr_fp

        def inner_fn(index):
            assert len(index) == len(ranges), f"wrong ndim {index} {ranges}"
            if dtype == torch.bool and override_fn_when_input_bool is not None:
                return override_fn_when_input_bool(*[load(index) for load in loaders])
            else:
                inputs_loaded = []
                for inp_index, load in enumerate(loaders):
                    out = load(index)
                    inp_dtype = inputs[inp_index].get_dtype()
                    if emulate_precision_casts and inp_dtype in low_pr_fp:
                        downcast = ops.to_dtype(out, inp_dtype, use_compute_types=False)
                        out = ops.to_dtype(downcast, inp_dtype)
                    inputs_loaded.append(out)

                out = fn(*inputs_loaded)
                if emulate_output_cast:
                    # fp16/bf16 kernels are computed in fp32. Casting down to fp16/bf16 here,
                    # then upcasting again, to emulate casts that eager would do.
                    downcast = ops.to_dtype(out, dtype, use_compute_types=False)
                    return ops.to_dtype(downcast, dtype)
                return out

        if not override_device:
            device = None
            for i in inputs:
                if is_gpu(i.get_device().type):
                    device = i.get_device()
                    break
            if not device:
                device = inputs[0].get_device()

        # pyrefly: ignore [unbound-name]
        device = override_device or device

        return Pointwise.create(
            device=device,  # type: ignore[arg-type]
            dtype=dtype,
            inner_fn=inner_fn,
            ranges=ranges,
        )