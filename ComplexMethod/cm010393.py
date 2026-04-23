def identify_accessed_tensors(
    kernel: "TritonKernelType",
    kwargs: dict[str, Any],
    tma_descriptor_metadata: TMADescriptorMetadata,
) -> TensorAccesses:
    """
    Given a triton kernel and the arguments for this kernel, this function
    1) Retrieves the TTIR converted version of the kernel from Triton's API.
    2) Parses the TTIR and creates a control flow graph
    3) Analyzes the graph to detect which input tensors are read and/or written
    """

    from torch._inductor.dependencies import Dep, ReadWrites, StarDep
    from torch._inductor.ir import TensorBox

    ttir_module = None
    functions = None
    try:
        ttir_module, ordered_arg_names = generate_ttir(
            kernel, kwargs, tma_descriptor_metadata
        )

        # extract functions from TTIR using MLIR bindings exposed by Triton code
        functions = ttir_to_functions(ttir_module)

        if functions is None:
            raise AssertionError("ttir_to_functions returned None")
        kernel_name = next(iter(functions.keys()))
        # Triton codegen modifies the name
        # pyrefly: ignore [missing-attribute]
        kernel_fn_name = kernel.fn.__name__
        if kernel_fn_name not in kernel_name:
            raise AssertionError(
                f"Kernel name {kernel_fn_name} not found in TTIR kernel name {kernel_name}"
            )
        # Reset the cache between top level invocations
        # The cache for analyze kernel access is mainly used for cycle
        # detection, so each top level invocation needs a clean cache
        analyze_kernel_access.reset()
        get_tma_stores.reset()

        # Build frozenset of indices corresponding to tensor args only.
        # Used to filter out scalars which are transitively captured as mutated
        # during traversal.
        tensor_arg_indices = frozenset(
            i
            for i, name in enumerate(ordered_arg_names)
            if isinstance(kwargs.get(name), (Tensor, TensorBox))
        )

        return analyze_kernel_access(
            functions,
            kernel_name,
            len(ordered_arg_names),
            tuple(ordered_arg_names),
            tensor_arg_indices,
        )
    except Exception:
        log.warning(
            "Encountered an exception in identify_accessed_tensors, assuming every input is mutated",
            exc_info=True,
        )
        if ttir_module is not None:
            log.debug("TTIR:\n%s", ttir_module)
        if functions is not None:
            log.debug("functions:")
            for name, fn in functions.items():
                log.debug("===\t%s\t===", name)
                for ret, ops in fn.items():
                    log.debug("%s\t=>\t%s", ret, ops)

        all_tensor_names = [
            key
            for key, value in kwargs.items()
            if isinstance(value, (Tensor, TensorBox))
        ]
        all_deps = OrderedSet(StarDep(name) for name in all_tensor_names)
        all_deps = typing.cast(OrderedSet[Dep], all_deps)
        return TensorAccesses(
            ReadWrites(
                reads=all_deps,
                writes=all_deps,
                index_exprs=OrderedSet(),
            ),
            can_fuse_epilogue=False,
        )