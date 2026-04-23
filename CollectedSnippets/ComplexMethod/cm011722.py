def finalize_multi_template_buffers(self) -> None:
        """
        Finalize a backing choice for MultiTemplateBuffers which did not already have a
        choice finalized through fusion. In the case of an extern choice, this will result
        in replacing the SchedulerNode.

        If a MultiTemplateBuffer did not have any fusion opportunities, finalizing a choice
        will force completion of compilation and benchmarking.
        """

        for i, node in enumerate(self.nodes):
            if isinstance(node, SchedulerNode) and isinstance(
                node.node, ir.MultiTemplateBuffer
            ):
                multi_node = node.node
                if not config.test_configs.force_extern_kernel_in_multi_template:
                    min_node_unfused, _ = multi_node.get_min_choice()
                else:
                    min_node_unfused = next(
                        (
                            timing
                            for timing in multi_node.choice_timings()
                            if isinstance(
                                timing,
                                torch._inductor.select_algorithm.ExternKernelCaller,
                            )
                        ),
                    )

                if isinstance(
                    min_node_unfused,
                    torch._inductor.ir.TritonTemplateCallerBase,
                ):
                    # Check for layout conflicts before committing to Triton template
                    if self._has_layout_conflict_for_template(multi_node):
                        # Fall back to first ExternKernelCaller (ATen)
                        for choice in multi_node.choice_timings():
                            if isinstance(
                                choice,
                                torch._inductor.select_algorithm.ExternKernelCaller,
                            ):
                                min_node_unfused = choice
                                break

                        assert isinstance(
                            choice, torch._inductor.select_algorithm.ExternKernelCaller
                        ), (
                            "No extern kernel detected to fallback to when layout constraints fail for Triton templates"
                        )

                if isinstance(
                    min_node_unfused,
                    torch._inductor.ir.TritonTemplateCallerBase,
                ):
                    # pyrefly: ignore [unbound-name]
                    if config.multi_kernel_hints:
                        callers: dict[int | None, TritonTemplateCallerBase] = {}
                        callers[None] = min_node_unfused

                        # pyrefly: ignore [unbound-name]
                        for hint in config.multi_kernel_hints:
                            timings = multi_node.choice_timings(hint_override=hint)
                            triton_timings = {
                                k: v
                                for k, v in timings.items()
                                if isinstance(k, TritonTemplateCallerBase)
                            }
                            choice = min(triton_timings.items(), key=lambda x: x[1])[0]
                            callers[hint] = choice

                        node.node.finalize_as_triton_callers(callers)
                    else:
                        node.node.finalize_as_triton_caller(min_node_unfused)
                    continue

                with ir.IRNode.current_origins(multi_node.origins):
                    out_tensorbox = min_node_unfused.output_node()
                out_storage = out_tensorbox.data  # type: ignore[union-attr]
                assert isinstance(out_storage, ir.StorageBox)
                out_buffer = out_storage.data
                assert isinstance(out_buffer, ir.OperationBuffer)

                if multi_node.origin_node:
                    assign_origin_node(out_tensorbox, multi_node.origin_node)

                out_buffer.layout = multi_node.layout
                self._replace_node(out_buffer, multi_node, i, node)