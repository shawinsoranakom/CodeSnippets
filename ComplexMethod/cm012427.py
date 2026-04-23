def codegen_loops_impl(self, loop_nest, code, worksharing):
        assert isinstance(self, CppKernelProxy)
        threads = parallel_num_threads()
        assert self.call_ranges is not None
        if isinstance(loop_nest.kernel, OuterLoopFusedKernel):
            par_depth = loop_nest.kernel.decide_parallel_depth(
                loop_nest.max_parallel_depth(), threads
            )
        else:
            par_depth = self.decide_parallel_depth(
                loop_nest.max_parallel_depth(), threads
            )

        is_reduction_loop = (
            loop_nest.loops is not None
            and loop_nest.loops[par_depth.start_depth].is_reduction
        )
        with contextlib.ExitStack() as stack:
            if par_depth.parallel_depth:
                if is_reduction_loop:
                    # need to close the worksharing scope to define reduction vars outside it
                    worksharing.close()
                else:
                    worksharing.parallel(threads)
                loop_nest.mark_parallel(par_depth)
            elif threads > 1:
                if worksharing.single():
                    stack.enter_context(code.indent())

            def gen_kernel(_loop_nest: LoopNest):
                def is_parallel_reduction():
                    assert _loop_nest.loops
                    root = _loop_nest.loops[par_depth.start_depth]
                    return root.is_reduction and root.parallel

                kernel = _loop_nest.get_kernel()
                if isinstance(kernel, OuterLoopFusedKernel):
                    for _loop_nest in kernel.inner:
                        gen_loop_nest(_loop_nest)
                else:
                    assert isinstance(kernel, CppKernelProxy)
                    if _loop_nest.loops is not None and is_parallel_reduction():
                        kernel.update_stores_with_parallel_reduction()
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(code.indent())
                        kernel.gen_body(code)

            def get_reduction_prefix_suffix(kernel, parallel=False, is_suffix=False):
                if is_suffix:
                    suffix = kernel.reduction_suffix
                    if parallel:
                        suffix = kernel.parallel_reduction_suffix + suffix
                    else:
                        suffix = kernel.non_parallel_reduction_suffix + suffix
                    return suffix
                else:
                    prefix = kernel.reduction_prefix
                    if parallel:
                        prefix = prefix + kernel.parallel_reduction_prefix
                    else:
                        prefix = prefix + kernel.non_parallel_reduction_prefix
                    return prefix

            def gen_loop_with_reduction(
                _loop_nest: LoopNest, depth: int = 0, in_reduction=False
            ):
                kernel = _loop_nest.get_kernel()
                assert _loop_nest.loops
                loop = _loop_nest.loops[depth]
                with contextlib.ExitStack() as stack_outer:
                    if loop.is_reduction and not in_reduction:
                        reduction_prefix = get_reduction_prefix_suffix(
                            kernel, loop.parallel, is_suffix=False
                        )
                        if reduction_prefix:
                            stack_outer.enter_context(code.indent())
                        code.splice(reduction_prefix)
                    if is_reduction_loop and loop.parallel:
                        worksharing.parallel(threads)
                        if kernel.local_reduction_init:
                            assert kernel.local_reduction_stores
                            code.splice(kernel.local_reduction_init)

                    gen_loop_at(_loop_nest, depth)

                    if is_reduction_loop and loop.parallel:
                        if kernel.local_reduction_stores:
                            code.splice(kernel.local_reduction_stores)
                        worksharing.close()
                    if loop.is_reduction and not in_reduction:
                        code.splice(
                            get_reduction_prefix_suffix(
                                kernel, loop.parallel, is_suffix=True
                            )
                        )

            def gen_loop_at(_loop_nest: LoopNest, depth: int = 0):
                with contextlib.ExitStack() as stack:
                    assert _loop_nest.loops
                    loop = _loop_nest.loops[depth]
                    loop_lines = loop.lines()
                    if loop_lines is None:
                        return
                    code.writelines(loop_lines)
                    stack.enter_context(code.indent())
                    gen_loop_nest(_loop_nest, depth + 1, loop.is_reduction)

            def gen_loop_nest(
                _loop_nest: LoopNest,
                depth: int = 0,
                in_reduction: bool = False,
            ):
                if _loop_nest.loops is None or depth == len(_loop_nest.loops):  # type: ignore[arg-type]
                    gen_kernel(_loop_nest)
                else:
                    gen_loop_with_reduction(_loop_nest, depth, in_reduction)

            stack.enter_context(code.indent())

            if (
                isinstance(loop_nest.kernel, OuterLoopFusedKernel)
                and isinstance(V.local_buffer_context, LocalBufferContext)
                and V.local_buffer_context.local_buffers
            ):
                # Allocate local buffer
                local_buffers = V.local_buffer_context.local_buffers
                for local_buffer in local_buffers.values():
                    # For dynamic size, rename s to ks
                    local_buf_size = sympy_product(
                        [
                            self.rename_indexing(size_val)
                            for size_val in local_buffer.get_layout().size
                        ]
                    )
                    local_buf_dtype = DTYPE_TO_CPP[local_buffer.get_layout().dtype]
                    allocate = f"std::make_unique<{local_buf_dtype} []>({cexpr(local_buf_size)})"
                    local_buffer_name = local_buffer.get_name()
                    code.splice(
                        f"std::unique_ptr<{local_buf_dtype} []> buf_{local_buffer_name} = {allocate};"
                    )
                    code.splice(
                        f"{local_buf_dtype}* {local_buffer_name} = buf_{local_buffer_name}.get();"
                    )
            gen_loop_nest(loop_nest)