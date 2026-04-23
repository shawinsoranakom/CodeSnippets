def _test_undefined_forward_mode(func, outputs, inputs):
    fwAD = torch.autograd.forward_ad

    _inp_tensors_idx, inp_tensors = _get_inp_tensors(inputs)
    _all_v, all_u, _all_u_dense = _make_vectors(
        inp_tensors, outputs, use_forward_ad=True
    )

    with fwAD.dual_level():
        fw_grads = []
        dual_inputs = []
        tensor_indices = set()
        for i, inp in enumerate(inputs):
            if is_tensor_like(inp) and inp.requires_grad:
                if inp.layout == torch._mkldnn:  # type: ignore[attr-defined]
                    raise ValueError(
                        "MKLDNN inputs are not support for forward AD gradcheck."
                    )

                inp = fwAD.make_dual(inp.detach(), torch.zeros_like(inp))
                # If inp is a differentiable view, the dual might not be the tangent given to
                # make_dual, so read it explicitly from the dual tensor
                fw_grads.append(fwAD.unpack_dual(inp)[1])
                tensor_indices.add(i)
            dual_inputs.append(inp)

        for fw_grad, u in zip(fw_grads, all_u):
            fw_grad.copy_(u.view_as(fw_grad))

        for idx, inp in enumerate(inputs):
            if idx not in tensor_indices:
                continue
            dual_inp_obj = dual_inputs[idx]

            # case 1 (Materialized Zero Tensor Tangent)
            dual_inputs[idx] = fwAD.make_dual(inp.detach(), torch.zeros_like(inp))
            raw_outputs = _as_tuple(func(*dual_inputs))
            dual_outputs1 = filter(_is_float_or_complex_tensor, raw_outputs)

            # case 2 (Efficient Zero Tensor Tangent since we don't make a dual object and pass a regular tensor)
            dual_inputs[idx] = inp.detach()
            raw_outputs = _as_tuple(func(*dual_inputs))
            dual_outputs2 = filter(_is_float_or_complex_tensor, raw_outputs)

            # reset
            dual_inputs[idx] = dual_inp_obj

            for index_o, (d_o1, d_o2) in enumerate(zip(dual_outputs1, dual_outputs2)):
                _val1, res1 = fwAD.unpack_dual(d_o1)
                _val2, res2 = fwAD.unpack_dual(d_o2)

                if not (res1 is None or res2 is None):
                    if not torch.allclose(res1, res2):
                        raise GradcheckError(
                            "Mismatch in tangent values for output with index: ",
                            index_o,
                            " when input: ",
                            inp,
                            " has an undefined tangent value. ",
                            " Got: ",
                            res1,
                            " but expected: ",
                            res2,
                        )
    return True