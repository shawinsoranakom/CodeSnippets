def _codegen(self, nodes: list[BaseSchedulerNode]) -> None:
        if config.check_stack_no_cycles_TESTING_ONLY:
            import torch._dynamo.convert_frame

            stack = traceback.extract_stack()
            seen: OrderedSet[tuple[str, int | None]] = OrderedSet()
            for frame in reversed(stack):
                # This is where maybe_cprofile is
                if (
                    frame.name == "_compile_inner"
                    and frame.filename == torch._dynamo.convert_frame.__file__
                ):
                    break
                key = (frame.filename, frame.lineno)
                assert key not in seen, (
                    f"Duplicate stack frame {frame.filename}:{frame.lineno}; "
                    "did you add a decorator to one of the functions in this stack "
                    "trace?  If so, try using a context manager instead."
                )
                seen.add(key)

        self.current_device = self.default_device_context
        assert self.previous_node is None

        # pyrefly: ignore [unbound-name]
        if self.default_device_context and config.triton.autotune_at_compile_time:
            V.graph.wrapper_code.write_get_raw_stream_header()

        # Register non-mutated inputs that need alignment checks.
        # Deferred to just before the first kernel that reads each input.
        V.graph.wrapper_code.register_alignment_check_inputs()

        for node in nodes:
            if log.isEnabledFor(logging.DEBUG):
                try:
                    log.debug(
                        "Generating code for node %s with estimated runtime %f",
                        node.get_name(),
                        node.get_estimated_runtime(),
                    )
                except Exception:
                    log.debug(
                        "Generating code for node %s with estimated runtime 0.0",
                        node.get_name(),
                    )

            self.enter_context(node)

            # pyrefly: ignore [unbound-name]
            if config.size_asserts:
                V.graph.wrapper_code.codegen_deferred_input_asserts(
                    dep.name for dep in node.read_writes.reads
                )

            if device := node.get_device():
                if (
                    device != self.current_device
                    or node.is_extern()
                    or node.is_template()
                ):
                    self.flush()
                if device != self.current_device:
                    if self.current_device and device_need_guard(
                        self.current_device.type
                    ):
                        # Exit stream context before exiting device guard
                        if self.current_stream_idx is not None:
                            self.generate_stream_ctx_exit()
                        V.graph.wrapper_code.codegen_device_guard_exit()
                    self.current_device = device
                    if device_need_guard(device.type):
                        assert device.index is not None, "device should have an index"
                        # Compute num_streams if we have multi-stream nodes
                        num_streams = 1
                        if self._has_multi_stream_nodes():
                            # Count unique streams (excluding default stream 0)
                            unique_streams = OrderedSet(self.node_to_stream.values())
                            num_streams = (
                                max(unique_streams) + 1 if unique_streams else 1
                            )
                        V.graph.wrapper_code.codegen_device_guard_enter(
                            device.index,
                            num_streams,
                            self.stream_idx_to_user_obj_idx,
                        )

            # Handle stream context switching for multi-stream scheduling.
            # This runs for all nodes (including device-less sync ops like
            # record_event/wait_event) so they are placed inside the correct
            # stream context. Only switch when inside a device guard (i.e.
            # current_device is set), since stream variables are declared there.
            if self._has_multi_stream_nodes() and self.current_device is not None:
                self.generate_stream_ctx_switching(node)

            # Emit deferred alignment copies for inputs first used by this
            # node.  This runs *after* stream context switching so the copy
            # executes on the same stream as the consuming kernel.
            # TODO: inputs read on multiple streams should be copied in the
            # prologue instead, to avoid cross-stream races.
            V.graph.wrapper_code.codegen_deferred_alignment_copies(
                dep.name for dep in node.read_writes.reads
            )

            self.current_node = node
            self.buffer_names_to_free.update(node.last_usage)

            if node.is_template():
                prologue, template_node, epilogue = node.get_prologue_template_epilogue(
                    list(node.get_nodes())
                )
                # pyrefly: ignore [unbound-name]
                self.get_backend(device).codegen_template(
                    template_node, epilogue, prologue
                )
            elif node.is_extern():
                self.codegen_extern_call(node)
            elif node.is_foreach():
                node = typing.cast(ForeachKernelSchedulerNode, node)
                # pyrefly: ignore [unbound-name]
                backend_ = self.get_backend(device)
                from .codegen.cuda_combined_scheduling import CUDACombinedScheduling
                from .codegen.simd import SIMDScheduling
                from .codegen.xpu.xpu_combined_scheduling import XPUCombinedScheduling

                if isinstance(
                    backend_,
                    (SIMDScheduling, CUDACombinedScheduling, XPUCombinedScheduling),
                ):
                    backend = backend_
                else:
                    raise AssertionError(f"{type(self)=}")
                backend.codegen_combo_kernel(node)
            elif isinstance(node, FusedMixOrderReductions):
                # pyrefly: ignore [unbound-name]
                self.get_backend(device).codegen_mix_order_reduction(node)
            elif isinstance(node, (FusedSchedulerNode, SchedulerNode)):
                # pyrefly: ignore [unbound-name]
                self.get_backend(device).codegen_node(node)
            else:
                assert isinstance(node, NopKernelSchedulerNode)
                node.mark_run()

            # pyrefly: ignore [unbound-name]
            if config.triton.debug_sync_kernel:
                # pyrefly: ignore [unbound-name]
                self.get_backend(device).codegen_sync()

            self.available_buffer_names.update(node.get_buffer_names())
            self.completed_operations.update(node.get_operation_names())

            if not isinstance(node, NopKernelSchedulerNode):
                device = node.get_device()
                if (
                    device is not None
                    and device.type != "meta"
                    and self.get_backend(device).ready_to_flush()
                ):
                    self.flush()

            if all(isinstance(n, SchedulerNode) for n in node.get_nodes()):
                self.previous_node = node
            else:
                self.previous_node = None

        if self.current_device != self.default_device_context:
            # when default_device_context is not None, we are codegen
            # for graph partitions and all nodes must be on
            # the same default device.
            assert self.current_device is not None
            if device_need_guard(self.current_device.type):
                # exit the outermost CUDA device guard. this is
                # important for nested indentation codegen-ing.
                V.graph.wrapper_code.codegen_device_guard_exit()

        self.previous_node = None
        self.flush()