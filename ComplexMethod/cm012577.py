def modification(self, subgraph_buffer, output_name, output_idx):
        assert isinstance(subgraph_buffer, ir.ComputedBuffer)
        subgraph_buffer_data = subgraph_buffer.data
        from ..loop_body import LoopBody
        from ..utils import sympy_index_symbol_with_prefix, SymT
        from ..virtualized import V
        from .cpp import CppKernelProxy, KernelGroup, ParallelDepth

        kernel_group = KernelGroup()
        kernel_input_args = {
            "score": "in_ptr0",
            "b": "in_ptr1",
            "h": "in_ptr2",
            "q_idx": "in_ptr3",
            "kv_idx": "in_ptr4",
        }
        if self.has_other_buffer:
            kernel_input_args.update(
                {arg: ptr for ptr, (_, arg) in self.other_ptr_data.items()}
            )

        kernel_output_args = {output_name: f"out_ptr{output_idx}"}

        args = kernel_group.args
        for name, inp in kernel_input_args.items():
            args.input_buffers[name] = inp

        for name, inp in kernel_output_args.items():
            args.output_buffers[name] = inp

        for name in self.extra_sizevars:
            args.sizevars[name] = f"k{name}"

        kernel_group.args = args

        cpp_kernel_proxy = CppKernelProxy(kernel_group)
        bodies = []
        var_sizes_list = []
        var_sizes = tuple(subgraph_buffer.get_size())
        var_ranges = {
            sympy_index_symbol_with_prefix(SymT.INDEX, i): sz
            for i, sz in enumerate(var_sizes)
        }

        dst_layout = subgraph_buffer.get_layout()
        output_index = dst_layout.make_indexer()([*var_ranges.keys()])

        def fn(*args):
            V.ops.store(
                output_name,
                output_index,
                subgraph_buffer_data.make_loader()(args).value,
            )

        body = LoopBody(
            fn,
            (list(var_ranges.keys())),
            var_ranges,
            list(var_ranges.keys()),
            tuple(),
        )

        from ..loop_body import MemoryUsageType

        assert all(
            mem.buffer_name in kernel_group.args.input_buffers
            for mem in body.memory_usage[MemoryUsageType.LOAD]
        ), (
            "All the buffers in the score and mask subgraph should be in kernel_group.args.input_buffers"
        )

        bodies.append(body)
        var_sizes_list.append((var_sizes, ()))

        cpp_kernel_proxy.codegen_loop_bodies(bodies, var_sizes_list)

        def max_parallel_depth():
            return ParallelDepth(parallel_depth=0, start_depth=0)

        # This loop is not parallelized since it is not the outermost loop.
        with patch.object(
            cpp_kernel_proxy.loop_nest, "max_parallel_depth", max_parallel_depth
        ):
            kernel_group.finalize_kernel(cpp_kernel_proxy, [])
        output_code = kernel_group.loops_code.getvalue()

        var_q_symbol, var_kv_symbol = self.block_vars
        # See [Note] Handle the case where the split sizes are not statically known.
        # We don't know the value of qBlockSize and rkvBlockSize during compilation time
        # thus we've represented them by symbols.
        # We change the symbol strings back to "cur_qSplitSize" and "cur_kvSplitSize"
        # in the generated code thus they'll be filled with the real value during runtime.
        if var_q_symbol in kernel_group.args.sizevars:
            output_code = output_code.replace(
                kernel_group.args.sizevars[var_q_symbol], "cur_qSplitSize"
            )
        if var_kv_symbol in kernel_group.args.sizevars:
            output_code = output_code.replace(
                kernel_group.args.sizevars[var_kv_symbol], "cur_kvSplitSize"
            )

        return output_code