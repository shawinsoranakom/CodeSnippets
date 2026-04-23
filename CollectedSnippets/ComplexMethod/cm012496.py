def store_pointwise_nodes(
        self,
        dst: ir.Buffer,
        nodes: list[ir.IRNode],
        offsets: list[sympy.Expr] | None = None,
        reindexers: list[Callable[[list[Any]], list[Any]] | None] | None = None,
    ) -> str:
        var_sizes = (tuple(dst.get_size()), ())
        var_ranges = {
            sympy_index_symbol_with_prefix(SymT.INDEX, i): sz
            for i, sz in enumerate(var_sizes[0])
        }
        if not offsets:
            offsets = [sympy.S.Zero] * len(var_sizes[0])
        if not reindexers:
            reindexers = [None] * len(nodes)
        assert len(offsets) == len(var_sizes[0])
        output_index = dst.get_layout().make_indexer()([*var_ranges.keys()])
        kernel_group = KernelGroup()
        kernel_group.args = self.args
        cpp_kernel_proxy = CppKernelProxy(kernel_group)
        bodies = []
        var_sizes_list = []
        for i, node in enumerate(nodes):
            output_name = node.get_name() if i < len(nodes) - 1 else dst.get_name()
            node = node.data if isinstance(node, ir.ComputedBuffer) else node
            assert isinstance(node, ir.Pointwise), node

            def fn(*args):
                assert len(args) == 2
                assert len(args[0]) == len(var_sizes[0])
                assert len(args[1]) == 0
                new_args = [arg + offset for arg, offset in zip(args[0], offsets)]  # type: ignore[arg-type]
                if reindexers[i] is not None:
                    new_args = reindexers[i](new_args)  # type: ignore[misc]
                V.ops.store(
                    output_name,
                    output_index,
                    node.make_loader()(new_args).value,
                )

            body = LoopBody(
                fn,
                (list(var_ranges.keys()), ()),
                var_ranges,
                list(var_ranges.keys()),
                tuple(),
            )
            bodies.append(body)
            var_sizes_list.append(var_sizes)

        cpp_kernel_proxy.codegen_loop_bodies(bodies, var_sizes_list)

        def max_parallel_depth():
            return ParallelDepth(parallel_depth=0, start_depth=0)

        # This loop is not parallelized since it is not the outermost loop.
        with patch.object(
            cpp_kernel_proxy.loop_nest, "max_parallel_depth", max_parallel_depth
        ):
            kernel_group.finalize_kernel(cpp_kernel_proxy, [])
        return kernel_group.loops_code.getvalue()