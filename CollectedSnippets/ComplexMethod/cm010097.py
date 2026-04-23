def activate_meta():
    activate_meta_table = {}

    # For a given op, we pick the most specific decomp function from
    # global_decomp_table in the precedence order of meta > post_autograd > pre_autograd
    for typ in ["meta", "post_autograd", "pre_autograd"]:
        registry = global_decomposition_table[typ]

        for opo in registry:
            if opo not in activate_meta_table:
                activate_meta_table[opo] = registry[opo]

    for op_overload, fn in activate_meta_table.items():
        # Don't register meta for HigherOrderOp's decomp.
        # We can reconsider this in the future, but in general,
        # the way you do a meta for a HigherOrderOp is different from
        # OpOverload.
        if isinstance(op_overload, torch._ops.HigherOrderOperator):
            continue
        if not isinstance(op_overload, OpOverload):
            raise AssertionError(
                f"op_overload must be OpOverload, got {type(op_overload)}"
            )

        op_overload.py_impl(torch._C.DispatchKey.Meta)(fn)

        if torch._C._dispatch_has_kernel_for_dispatch_key(
            op_overload.name(), "CompositeImplicitAutograd"
        ):
            # Internally, we shouldn't be registering meta kernels for any operators that
            # have CompositeImplicitAutograd kernels.
            # Instead, we should be letting those decompositions run, and writing meta kernels
            # only for the base operators.
            if op_overload in global_decomposition_table["meta"]:
                raise RuntimeError(
                    f"{op_overload} is a CompositeImplicitAutograd op, we shouldn't "
                    "register meta function for it. Instead, we should let the decomposition run and write "
                    "meta kernels for the base operators."
                )
        elif op_overload.is_view:
            # Attempting to register a python meta kernel for a view operator.
            # We shouldn't do this, because the output will report as not having aliased storages.
            # All view ops have meta kernels in C++ today, so we should use those instead.
            pass
        elif (
            op_overload.name()
            in {
                "aten::empty_strided",  # causing infinite recursion, test_meta.py
                "aten::clone",  # causing infinite recursion
                "aten::_to_copy",  # causing infinite recursion, test_serialization.py -k test_tensor_subclass_getstate_overwrite
                "aten::copy_",  # Exception not raised, test_torch.py -k test_storage_meta_errors_cpu_int64
                "aten::constant_pad_nd",  # requires_grad mismatch, test_ops.py -k test_fake_crossref_backward_amp_istft_cuda_float32
                "aten::rot90",  # requires_grad mismatch! test_ops.py -k test_fake_crossref_backward_amp_rot90_cuda_float32
                "aten::as_strided_scatter",  # requires_grad mismatch, test_ops.py -k test_fake_crossref_backward_no_amp_as_strided_scatter_cuda_float32
            }
        ):
            pass
        else:
            if "mkldnn::" in op_overload.name():
                _meta_lib_dont_use_me_use_register_meta_for_mkldnn.impl(op_overload, fn)
            elif "mkl::" in op_overload.name():
                _meta_lib_dont_use_me_use_register_meta_for_mkl.impl(op_overload, fn)
            elif "onednn::" in op_overload.name():
                _meta_lib_dont_use_me_use_register_meta_for_onednn.impl(op_overload, fn)
            elif "quantized::" in op_overload.name():
                _meta_lib_dont_use_me_use_register_meta_for_quantized.impl(
                    op_overload, fn
                )
            else:
                _meta_lib_dont_use_me_use_register_meta.impl(op_overload, fn)