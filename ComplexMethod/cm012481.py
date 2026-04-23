def generate_example_arg_value(self, arg, arg_type, raw_arg=None):
        if isinstance(arg_type, torch_dtype):
            if isinstance(raw_arg, ir.TMADescriptor):
                # first we generate the underlying buffer
                buf_name = raw_arg.get_tensor().get_name()
                buf = self.args_to_buffers[arg]
            elif self.args_to_buffers.get(arg):
                buf_name = arg
                buf = self.args_to_buffers[arg]
            else:
                assert raw_arg is not None, (
                    "V.graph.get_buffer(arg) and raw_arg can't be None at the same time"
                )
                buf_name = f"tmp_arg_{self.kernel_autotune_tmp_arg_idx}"
                buf = raw_arg
                self.kernel_autotune_tmp_arg_idx += 1

            assert buf is not None, f"Failed to find a buffer for arg {arg}"
            size = V.graph.sizevars.optimization_hints(buf.get_size())
            allocation_size = V.graph.sizevars.optimization_hints(
                V.graph.get_allocation_size(buf)
            )
            stride = V.graph.sizevars.optimization_hints(buf.get_stride())

            device = buf.get_device()
            dtype = buf.get_dtype()
            offset = V.graph.sizevars.optimization_hint(buf.get_layout().offset)
            value = f"generate_example_value({size}, {stride}, '{device}', {dtype}, {offset}, {allocation_size})"
            self.kernel_autotune_calls.writeline(f"{buf_name} = {value}")

            if isinstance(raw_arg, ir.TMADescriptor):
                # generate another line initializing a host-side TMA
                # descriptor from the underlying buffer created above
                value = self._generate_tma_descriptor_call(
                    desc=raw_arg,
                    apply_size_hints=True,
                )
                buf_name = arg
                self.kernel_autotune_calls.writeline(f"{buf_name} = {value}")

            return buf_name
        elif issubclass(arg_type, sympy.Basic) or isinstance(arg, SymbolicCallArg):
            # arg is a symbol or symbolic expression
            if isinstance(arg, str):
                if arg in self._meta_vars:
                    return arg
                if raw_arg is None:
                    return "None"
                arg = raw_arg
            if isinstance(arg, SymbolicCallArg):
                arg = arg.inner_expr
            if arg in V.graph.sizevars.inv_precomputed_replacements:
                arg = V.graph.sizevars.inv_precomputed_replacements[arg]

            return str(V.graph.sizevars.optimization_hint(arg))

        elif isinstance(arg, (str, int, float, bool)):
            return str(arg)
        elif isinstance(arg, list):
            return f"[{', '.join(self.generate_example_arg_value(a, type(a)) for a in arg)}]"
        else:
            raise NotImplementedError(f"Unsupported type {type(arg)}")