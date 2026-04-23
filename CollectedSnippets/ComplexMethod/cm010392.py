def analyze_kernel_access(
    functions: dict[str, dict[Intermediate, list[Op]]],
    fn_name: str,
    num_args: int,
    tensor_names: tuple[str, ...],
    tensor_arg_indices: frozenset[int] | None,
) -> TensorAccesses:
    """
    Analyzes the graph to detect which arguments are written to and which are read.

    For writes: traverses from write sinks (tt.store, tt.atomic_cas, etc.) backwards
    to identify input pointers that are written to.

    For reads: traverses from read operations (tt.load) backwards to identify
    input pointers that are read from.

    Returns ReadWrites with StarDep objects for each accessed tensor.
    """
    from torch._inductor.dependencies import Dep, ReadWrites, StarDep

    # Name of mutation op to mutated parameter indices
    # List from Triton Github include/triton/Dialect/Triton/IR/TritonOps.td
    # All the OPs that have MemWrite trait.
    # What if Triton exposed this?
    WRITE_OPS = {
        "tt.store": [0],
        "tt.atomic_cas": [0],
        "tt.atomic_rmw": [0],
        "tt.experimental_descriptor_store": [0],
        "tt.experimental_tensormap_create": [0],
        "tt.descriptor_store": [0],
    }
    READ_OPS = {
        "tt.load": [0],
        "tt.load_tensor_descriptor": [0],
        "tt.descriptor_load": [0],
    }
    UNKNOWN_OPS = {"tt.elementwise_inline_asm"}

    write_stack: list[Param | Intermediate] = []
    read_stack: list[Param | Intermediate] = []

    ops = functions[fn_name]
    tma_stores = get_tma_stores(functions, fn_name)

    for op_list in ops.values():
        for op in op_list:
            # If we encounter an operation with effects that cannot be reliably analyzed
            # (e.g. `tt.elementwise_inline_asm`), we assume it does not mutate any input parameters.
            if op.name in UNKNOWN_OPS:
                if op.name == "tt.elementwise_inline_asm" and op.is_pure:
                    continue
                raise RuntimeError(
                    f"ttir analysis hit an op we do not know how to analyze: {op.name}"
                )

            if op.name == "tt.experimental_tensormap_create":
                # Note: this is how we implement experimental_descriptor_store mutation analysis.
                # for on-device TMA.
                # experimental_tensormap_store(a, b, ...) stores b to the location specified
                # by descriptor in the memory of a.
                # To track this, we first find all the intermediates/params to which we store via
                # experimental_tensormap_store (get_tma_stores, called above). Then, during this
                # analysis we wait to find the corresponding experimental_tensormap_create (if it
                # exists), at which point we will mark the global_ptr as mutated (as done below).
                if len(op.args) < 2:
                    raise AssertionError(
                        f"tt.experimental_tensormap_create expected at least 2 args, "
                        f"got {len(op.args)}"
                    )
                if op.args[0] in tma_stores:
                    write_stack.append(op.args[1])

            if op.name == "tt.call":
                if op.fn_call_name not in functions:
                    raise AssertionError(
                        f"Function {op.fn_call_name} not found in functions dict"
                    )
                # Create placeholder names for nested function arguments
                nested_names = tuple(f"_arg{i}" for i in range(len(op.args)))

                # Do not pass tensor_arg_indices, most outer call of
                # analyze_kernel_access will filter Param nodes.
                accesses = analyze_kernel_access(
                    functions,
                    # pyrefly: ignore [bad-argument-type]
                    op.fn_call_name,
                    len(op.args),
                    nested_names,
                    None,
                )
                # Map back from StarDep names to args
                written_set = {dep.name for dep in accesses.read_writes.writes}
                read_set = {dep.name for dep in accesses.read_writes.reads}
                for arg, name in zip(op.args, nested_names):
                    if name in written_set:
                        write_stack.append(arg)
                    if name in read_set:
                        read_stack.append(arg)
            else:
                write_stack.extend(op.args[idx] for idx in WRITE_OPS.get(op.name, []))
                read_stack.extend(op.args[idx] for idx in READ_OPS.get(op.name, []))

    # For these ops, only the first argument (base pointer) refers to actual
    # memory. The remaining arguments are shape/stride/offset metadata and
    # should not be traced during mutation analysis.
    POINTER_ONLY_OPS = {
        "tt.make_tensor_ptr",
        "tt.advance",
        "tt.make_tensor_descriptor",
    }

    def _find_arg_access_count(
        initial_stack: list[Param | Intermediate],
        skip_loads: bool,
    ) -> dict[int, int]:
        """DFS traversal to find argument indices that are accessed (and how many times they are accessed)."""
        access_count = dict()
        stack = initial_stack[:]

        while stack:
            arg = stack.pop()

            if isinstance(arg, Param):
                if arg.idx >= num_args:
                    continue
                if tensor_arg_indices is not None and arg.idx not in tensor_arg_indices:
                    continue
                if arg.idx not in access_count:
                    access_count[arg.idx] = 1
                else:
                    access_count[arg.idx] += 1
            elif isinstance(arg, Intermediate) and not arg.fake():
                for op in ops[arg]:
                    if skip_loads and op.name == "tt.load":
                        continue
                    if op.name in POINTER_ONLY_OPS:
                        stack.append(op.args[0])
                    else:
                        stack.extend(op.args)

        return access_count

    write_count = _find_arg_access_count(write_stack, skip_loads=True)
    read_count = _find_arg_access_count(read_stack, skip_loads=False)

    writes: OrderedSet[Dep] = OrderedSet(
        StarDep(tensor_names[i]) for i in sorted(write_count.keys())
    )
    reads: OrderedSet[Dep] = OrderedSet(
        StarDep(tensor_names[i]) for i in sorted(read_count.keys())
    )

    read_writes = ReadWrites(
        reads=reads,
        writes=writes,
        index_exprs=OrderedSet(),
    )

    def _decide_can_fuse_epilogue():
        # only do epilogue fusion if the kernel has a single output tensor
        if len(write_count) != 1:
            return False

        written_arg_index = next(iter(write_count))
        # only do epilogue fusion if the written tensor is written exactly once
        if write_count[written_arg_index] != 1:
            return False

        written_arg_name = next(iter(writes)).name
        #  cannot fuse if the kernel also reads from the output buffer
        if any(read_dep.name == written_arg_name for read_dep in reads):
            return False

        return True

    can_fuse_epilogue = _decide_can_fuse_epilogue()

    return TensorAccesses(read_writes=read_writes, can_fuse_epilogue=can_fuse_epilogue)