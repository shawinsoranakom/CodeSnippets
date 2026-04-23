def _generate_kernel_call_helper(
        self,
        kernel_name: str,
        call_args,
        *,
        device=None,
        triton=True,
        arg_types=None,
        raw_keys=None,
        raw_args=None,
        triton_meta=None,
        inductor_meta=None,
        graph_name="",
        original_fxnode_name=None,
        current_stream_idx=None,
    ):
        device = device or V.graph.get_current_device_or_throw()
        if not triton and device.type not in ("cuda", "xpu"):
            if device.type == "cpu":
                self.writeline(self.wrap_kernel_call(kernel_name, call_args))
            elif device.type == "mps":
                # TODO: Fix me, MPS does not expose streams now
                self.writeline(self.wrap_kernel_call(kernel_name, call_args))
            else:
                raise RuntimeError(f"device {device.type} nyi")
            return

        call_args_str = self.prepare_triton_kernel_call(call_args)
        call_args_str = ", ".join(call_args_str)
        if current_stream_idx is not None and current_stream_idx != DEFAULT_STREAM_IDX:
            # Inside a user stream context: emit a fresh get_raw_stream call so
            # it picks up the active stream at runtime, rather than reusing the
            # LRU-cached stream0 variable which captured the default stream.
            self.write_get_raw_stream_header()
            stream_name = "raw_stream"
            self.writeline(f"{stream_name} = get_raw_stream({device.index})")
        else:
            stream_name = PythonWrapperCodegen.write_get_raw_stream(
                self, device.index, graph_name
            )
        if not triton:
            stream_ptr = f"c_void_p({stream_name})"
            self.writeline(
                f"{kernel_name}.{kernel_name}({call_args_str}, {stream_ptr})"
            )
            return

        self.write_triton_header_once()

        if (
            config.triton.autotune_at_compile_time
            and kernel_name not in self.kernel_autotune_names
        ):
            # Create example args for autotune in a separate epilogue
            assert arg_types is not None and len(call_args) == len(arg_types), (
                "call_args and arg_types do not match"
            )

            autotune_args = None
            if original_fxnode_name and V.graph.autotuning_mapping:
                autotune_args = V.graph.autotuning_mapping.get(
                    original_fxnode_name, None
                )

            def get_autotune_deletion_call() -> str:
                """After all the autotune kernel calls have been written (i.e.
                self.kernel_autotune_example_args is complete), returns a deletion call
                for all autotune example tensors that are unnecessary after kernel_name
                is called."""
                tensors_to_delete = [
                    tensor
                    for tensor, kn in self.kernel_autotune_example_args.values()
                    if kn == kernel_name
                ]
                if tensors_to_delete:
                    return f"del {', '.join(tensors_to_delete)}\n"
                return ""

            def infer_arg_by_inputs(raw_keys, raw_args, idx, reused_args):
                """We try to infer raw_arg (i.e. raw_args[idx]) from remaining raw_args.
                This is particularly useful for jagged cases, where the dimension is often
                being passed in as an input."""

                target_arg = raw_args[idx]
                if target_arg in reused_args:
                    return True

                for i, (raw_key, raw_arg) in enumerate(zip(raw_keys, raw_args)):
                    if i == idx or not isinstance(raw_arg, IRNode):
                        continue

                    triton_input = ""
                    if autotune_args and raw_key in autotune_args:
                        triton_input = self.get_autotuning_input_name(  # type: ignore[attr-defined]
                            autotune_args[raw_key]
                        )
                    if triton_input == "":
                        continue

                    try:
                        layout = raw_arg.get_layout()
                        for dim, s in enumerate(layout.size):
                            if s == target_arg:
                                reused_args[target_arg] = f"{triton_input}.shape[{dim}]"
                                return True
                    except NotImplementedError:
                        # If layout for this IRNode is not implemented, we could just skip.
                        # Only raise for other Error cases.
                        continue
                return False

            all_args = []
            if raw_args is None:
                # create a dummy raw_args for uniform behavior in the following loop
                assert raw_keys is None, "keys are not None but args are"
                raw_keys = [None] * len(call_args)
                raw_args = [None] * len(call_args)
            else:
                assert len(raw_args) == len(call_args), (
                    "call_args and raw_args do not match"
                )

            reused_args = {}
            for i, (arg, arg_type, raw_key, raw_arg) in enumerate(
                # pyrefly: ignore [bad-argument-type, no-matching-overload]
                zip(call_args, arg_types, raw_keys, raw_args)
            ):
                key = None
                if isinstance(arg, str) and "=" in str(arg):
                    # arg may be passed in a kwarg style, and then we need to extract its value
                    key, arg = arg.split("=")

                triton_input: str | None = None
                if autotune_args and raw_key in autotune_args:
                    triton_input = self.get_autotuning_input_name(  # type: ignore[attr-defined]
                        autotune_args[raw_key]
                    )

                if triton_input:
                    arg_str = triton_input
                    if not isinstance(arg_type, torch_dtype) and (
                        issubclass(arg_type, sympy.Basic)
                        or isinstance(arg, SymbolicCallArg)
                    ):
                        reused_args[raw_arg] = arg_str
                elif raw_key == "" and infer_arg_by_inputs(
                    raw_keys, raw_args, i, reused_args
                ):
                    # Empty raw_key means this is a arg that's not native to the triton kernel,
                    # and is being added by inductor.
                    arg_str = reused_args[raw_arg]
                elif isinstance(arg_type, torch_dtype):
                    # workspace allocation is already generated by `generate_workspace_allocation()`
                    # in `TritonKernel.call_kernel()`.
                    if re.match(r"^(workspace|semaphore)", arg):
                        arg_str = arg
                    elif arg not in self.kernel_autotune_example_args:
                        arg_str = self.generate_example_arg_value(
                            arg, arg_type, raw_arg
                        )
                    else:
                        arg_str = self.kernel_autotune_example_args[arg][0]
                    self.kernel_autotune_example_args[arg] = (arg_str, kernel_name)
                else:
                    arg_str = self.generate_example_arg_value(arg, arg_type, raw_arg)

                if isinstance(arg, str) and should_unwrap_unspec_arg(arg):
                    arg_str += ".item()"
                all_args.append(arg_str if key is None else f"{key}={arg_str}")

            # Make sure kernel launch under a device guard because models don't always run on device 0
            self.kernel_autotune_calls.writeline(
                f"with {V.graph.device_ops.device_guard(device.index)}:"
            )
            self.kernel_autotune_calls.do_indent()
            self.kernel_autotune_calls.writeline(
                f"{kernel_name}.run({', '.join(all_args)}, stream={stream_name})"
            )
            self.kernel_autotune_calls.do_unindent()

            self.kernel_autotune_calls.writeline(
                DelayReplaceLine("<del_call>", get_autotune_deletion_call, "<del_call>")
            )
            self.kernel_autotune_names.add(kernel_name)
            if V.graph.cpp_wrapper:
                # For cpp wrapper, no need to continue codegen for the main body
                return

        # add debug printer code for triton kernel calls at (jit) inductor level
        debug_printer_manager = V.graph.wrapper_code.debug_printer
        debug_printer_manager.set_printer_args(call_args, kernel_name, arg_types, None)
        with debug_printer_manager:
            self.writeline(f"{kernel_name}.run({call_args_str}, stream={stream_name})")
        self.write_triton_header_once()