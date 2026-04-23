def specialize(value: torch.Tensor) -> dict[str, Any]:
        props: dict[str, Any] = {
            "dtype": value.dtype,
            "device": value.device,
            "layout": value.layout,
            "ndim": int(value.ndim),
            "requires_grad": value.requires_grad,
            "is_nested": value.is_nested,
            "is_quantized": value.is_quantized,
            "is_sparse": value.is_sparse,
            "class_type": type(value),
        }
        try:
            props["has_grad_fn"] = value.grad_fn is not None
        except Exception:
            # Workaround for issues with create_parameter_op in Dynamo. Reading
            # grad_fn should never cause an issue.
            props["has_grad_fn"] = False

        if is_sparse_any(value) and not has_free_symbols(value):
            props["_size"] = tuple(
                int(s) if is_symbolic(s) else s for s in value.size()
            )
        elif not has_free_symbols(value):
            # this is a fully static shape, and the keys on props here inform specialization.
            # We have to cast to int here, because these might get accessed as ConstantVariable, which has
            # a strict no-symint policy. If we got here due to not having free symbols, this is a known constant
            # already. We could remove the discrepancy here, by having ConstantVariable be more permissive for
            # constant backed SymInts, but that assert being strict has led to some good signal in hunting bugs, and
            # I'd like to keep it around for now.
            props["_size"] = tuple(
                # the non is_symbolic case applies to the jagged layout
                # NestedTensor case as singleton ints are not symbolic
                int(s) if is_symbolic(s) else s
                for s in value.size()
            )
            props["stride"] = tuple(value.stride())
            if torch._C._functorch.is_batchedtensor(value):
                # Batched tensors does not support contiguity patterns, so
                # we refrain from computing the `is_contiguous` property
                props["is_contiguous"] = None
            else:
                props["is_contiguous"] = tuple(
                    x
                    for x in torch._prims_common._memory_formats
                    if value.is_contiguous(memory_format=x)
                )
        return props