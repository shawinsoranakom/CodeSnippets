def codegen_kernel_benchmark(self, num_gb: float) -> IndentedBuffer:
        """
        Generates Python code for benchmarking this combo kernel.
        - Creates example inputs (random tensors, constants, sizes).
        - Runs the kernel on the current GPU/stream.
        - Prints runtime (ms) and throughput (GB/s) using `num_gb`.
        Args:
            num_gb (float): The number of gigabytes to use for throughput calculation.
        Returns:
            IndentedBuffer: A buffer containing the generated Python benchmark code.
        """
        result = IndentedBuffer()
        _argdefs, call_args, signature, _ = self.args.python_argdefs()
        result.writelines(["", "", "def get_args():"])
        with result.indent():
            name_cnt = itertools.count()
            var_names = []
            for arg_name, arg_sig in zip(call_args, signature):
                var_name = f"arg_{next(name_cnt)}"
                buf = V.graph.try_get_buffer(arg_name)
                if buf:
                    size = V.graph.sizevars.optimization_hints(buf.get_size())
                    stride = V.graph.sizevars.optimization_hints(buf.get_stride())
                    result.writeline(
                        f"{var_name} = rand_strided({size}, {stride}, device='{buf.get_device()}', dtype={buf.get_dtype()})"
                    )
                elif arg_name in V.graph.constants:
                    # note that random seed is put in V.graph.constants
                    const_tensor = V.graph.constants[arg_name]
                    size = V.graph.sizevars.optimization_hints(const_tensor.size())
                    stride = V.graph.sizevars.optimization_hints(const_tensor.stride())
                    result.writeline(
                        f"{var_name} = rand_strided({size}, {stride}, device='{const_tensor.device}', dtype={const_tensor.dtype})"  # type: ignore[arg-type]
                    )
                elif isinstance(arg_sig, SizeArg):
                    symval_hint = V.graph.sizevars.optimization_hint(arg_sig.expr)

                    # Force the seed_offset to be 0 so calls to the same kernel
                    # using different seed offset will have the same benchmark harness.
                    # We can dedup kernel definitions in this case.
                    if "seed_offset" in arg_sig.name:
                        symval_hint = 0
                    result.writeline(f"{var_name} = {symval_hint}")
                elif isinstance(arg_sig, WorkspaceArg):
                    device = V.graph.get_current_device_or_throw()
                    count = V.graph.sizevars.optimization_hint(arg_sig.count)
                    # for benchmark harness, we ignore arg_sig.zero_mode and always zero it
                    result.writeline(
                        f"{var_name} = torch.zeros({count}, device='{device}', dtype={arg_sig.dtype})"
                    )
                else:
                    raise KeyError(
                        f"Don't find the buffer or const tensor for {arg_name}"
                    )
                var_names.append(var_name)
            if self.dynamic_shape_args:
                var_names.extend(self.kernel_benchmark_extra_args())
            result.writeline(f"return {', '.join(var_names)},")

        result.writelines(["\n", "\n", "def call(args):"])
        device = V.graph.get_current_device_or_throw()
        index = V.graph.get_current_device_or_throw().index
        with result.indent():
            result.writeline(f"with {V.graph.device_ops.device_guard(index)}:")
            with result.indent():
                result.writeline(
                    V.graph.device_ops.set_device(index)
                )  # no-op to ensure context
                stream_name = f"stream{index}"
                result.writeline(f"{stream_name} = get_raw_stream({index})")
                result.writeline(
                    f"{str(Placeholder.KERNEL_NAME)}.run(*args, stream={stream_name})"
                )

        # benchmark all configs
        result.writelines(["\n", "\n", "def benchmark_all_configs(args):"])
        with result.indent():
            result.writeline(f"with {V.graph.device_ops.device_guard(index)}:")
            with result.indent():
                result.writeline(
                    V.graph.device_ops.set_device(index)
                )  # no-op to ensure context
                result.writeline(
                    f"return {str(Placeholder.KERNEL_NAME)}.benchmark_all_configs(*args)"
                )

        result.writelines(["\n", "\n", "if __name__ == '__main__':"])
        with result.indent():
            result.writeline(
                "from torch._inductor.runtime.benchmarking import benchmarker"
            )
            result.writeline("")

            result.writeline("args = get_args()")
            result.writeline(
                f"ms = benchmarker.benchmark(call, fn_args=(args,), device={device.type},rep=40)"
            )
            result.writeline(f"num_gb = {num_gb}")
            result.writeline("gb_per_s = num_gb / (ms / 1e3)")
            result.writeline(
                'print(f"{ms:.3f}ms    {num_gb:.3f}GB    {gb_per_s:.2f}GB/s")'
            )

        return result