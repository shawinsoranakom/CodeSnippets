def _init(self, nodes: list[ir.Operation]) -> None:
        super().__init__()
        V.graph.scheduler = self
        self.backends: dict[torch.device, BaseScheduling] = {}
        self.post_grad_graph_id = next(_post_grad_graph_counter)
        self._graph_partition_counter = itertools.count()

        self.completed_operations: OrderedSet[str] = OrderedSet()
        self.available_buffer_names = OrderedSet(
            [
                *V.graph.graph_inputs.keys(),
                *V.graph.constants.keys(),
                *V.graph.torchbind_constants.keys(),
            ]
        )
        self.nodes = [self.create_scheduler_node(n) for n in nodes]
        self.previous_node: BaseSchedulerNode | None = None
        self.current_node: BaseSchedulerNode | None = None
        self.update_zero_dim_cpu_tensor()
        # some new constants could have been created above
        self.available_buffer_names.update(V.graph.constants.keys())
        for node in self.nodes:
            node.prune_deps()

        # See [Note: Graph Partition Device Contexts]
        self.default_device_context: torch.device | None = None

        self.name_to_donated_buffer: dict[str, SchedulerDonatedBuffer] = (
            self.get_donated_buffers()
        )
        self.name_to_node: dict[str, BaseSchedulerNode] = {
            n.get_name(): n for n in self.nodes
        }

        self.name_to_buf: dict[str, SchedulerBuffer] = {
            buf.get_name(): buf for node in self.nodes for buf in node.get_outputs()
        }
        self.name_to_fused_node: dict[str, BaseSchedulerNode] = self.name_to_node.copy()

        # mutation_real_name: Maps back to the original name for codegen
        # Example:
        # If you mutate buf0 inside of buf1's kernel, then:
        # mutation_real_name = {"buf0" : "buf1"}
        # all subsequent uses of buf0 become buf1's usage in dependency graph
        self.mutation_real_name: dict[str, str] = {}

        # We handle mutation by renaming modified versions of the same
        # buffer in the dependency graph to prevent cycles.
        # mutation_renames: tracks the current name for a given buffer
        #                   (changed once per mutation)
        # Example:
        # If you mutate buf0 inside of buf1's kernel, then:
        # mutation_renames = {"buf1" : "buf0"}
        # in codegen we only use buf0, never buf1
        self.mutation_renames: dict[str, str] = {}

        self.seen_template_fusions: OrderedSet[
            tuple[BaseSchedulerNode, BaseSchedulerNode]
        ] = OrderedSet()
        # Must run first to correctly set dependencies, before all other passes that rely on
        # reading from .read_writes.reads or .unmet_dependencies
        self.nodes = comms.decide_global_ordering_of_comms(
            self.nodes,
            self.name_to_buf,
            self.name_to_fused_node,
        )

        self.compute_dependencies()
        self.nodes = self.topological_sort_schedule(self.nodes)
        self.dead_node_elimination()
        self.name_to_fused_node = {n.get_name(): n for n in self.nodes}
        self.compute_ancestors()
        self.compute_input_distances()

        # pyrefly: ignore [bad-assignment]
        metrics.ir_nodes_pre_fusion += len(self.nodes)
        from torch._inductor.debug import log_ir_post_fusion, log_ir_pre_fusion

        log_ir_pre_fusion(self.nodes)
        self.num_orig_nodes = len(self.nodes)
        self.create_foreach_nodes()
        self.nodes = self.topological_sort_schedule(self.nodes)
        self.logged_slow_fusion = OrderedSet[tuple[str, str]]()
        if config._pre_fusion_custom_pass is not None:
            self.nodes = config._pre_fusion_custom_pass(self.nodes)

        if config.distributed_max_autotune_gemm:
            from . import distributed_autotune

            distributed_autotune.schedule(self)
            self.compute_ancestors()

        # Stream assignments must be populated BEFORE fusion
        # to prevent fusing nodes across stream boundaries
        self.node_to_stream: dict[BaseSchedulerNode, int] = {}
        self.buff_to_stream: dict[str, int] = {}
        self._multi_stream_nodes: bool = False
        # Maps stream_idx → user_object_index for retrieving user stream objects
        self.stream_idx_to_user_obj_idx: dict[int, int] = {}
        self._populate_stream_assignments()

        self.nodes = self.fuse_nodes(self.nodes)
        if config._post_fusion_custom_pass is not None:
            self.nodes = config._post_fusion_custom_pass(self.nodes)

        if any(
            isinstance(node, FusedExternTritonKernelSchedulerNode)
            for node in self.nodes
        ):
            # if a user triton kernel has been epilogue-fused,
            # there is likely an opportunity to prune an NopKernel
            # (which is originally used to generate the buffer which the triton kernel writes to)
            self.dead_node_elimination()

        self.merge_loops()
        self.finalize_multi_template_buffers()
        if (
            config.max_autotune_gemm or config.max_autotune
        ) and use_pipelined_autotuning():
            torch._inductor.select_algorithm.PrecompileThreadPool.shutdown_instance()

        if config.combo_kernels:
            with dynamo_timed(
                "Scheduler.create_combo_kernel_nodes",
                log_pt2_compile_event=True,
                log_waitcounter=True,
            ):
                self.create_combo_kernel_nodes(num_ck_nodes=None)

        # torch.cond can contain arbitrary subgraphs, which can contain collectives
        # reordering these can cause a nccl hang
        self._enforce_conditional_ordering()

        # Peak memory pass and overlap pass must run last, otherwise
        # other reordering passes could undo their effects.
        if config.reorder_for_peak_memory:
            from .memory import reorder_for_peak_memory

            self.nodes = reorder_for_peak_memory(
                self.nodes,
                self.name_to_buf,
                self.name_to_fused_node,
                OrderedSet(V.graph.graph_inputs.keys()),
                OrderedSet(V.graph.get_output_names()),
            )

        # reorder_for_compute_comm_overlap may do benchmarking to estimate
        # op runtime. Disable it for now in deterministic mode.
        if not config.deterministic and config.reorder_for_compute_comm_overlap:
            if not config.reorder_for_peak_memory:
                from .memory import assign_memory_planning_info_for_scheduler_buffers

                assign_memory_planning_info_for_scheduler_buffers(
                    self.nodes, self.name_to_buf
                )

            if (
                used_non_deterministic_runtime_estimations()
                and config_comms.runtime_estimations_align_across_all_distributed_ranks
                and (
                    config.runtime_estimations_mms_benchmark
                    or config_comms.runtime_estimations_use_nccl_lib_estimations
                )
            ):
                has_collectives = False
                for node in self.nodes:
                    if is_collective(node.node):
                        has_collectives = True
                        break
                if has_collectives:
                    from .comms import (
                        align_runtime_estimations_across_all_distributed_ranks,
                    )

                    align_runtime_estimations_across_all_distributed_ranks(self.nodes)

            # pyrefly: ignore [unbound-name]
            if config_comms.reorder_sink_verbose_logging:
                from torch._logging import trace_structured

                trace_structured(
                    "artifact",
                    metadata_fn=lambda: {
                        "name": "scheduler_nodes_before_comm_overlap",
                        "encoding": "string",
                    },
                    payload_fn=lambda: "\n\n".join(
                        [
                            f"snode[{i}]"
                            + n.debug_str()
                            + f" buffer_names:{n.get_buffer_names()}"
                            for i, n in enumerate(self.nodes)
                        ]
                    ),
                )
            self.nodes = comms.reorder_compute_and_comm_for_overlap(self.nodes)
        self.process_grouped_nodes()

        if (
            # pyrefly: ignore[unbound-name]
            config.graph_partition
            # pyrefly: ignore[unbound-name]
            and config.triton.cudagraphs
            # pyrefly: ignore[unbound-name]
            and config.triton.reorder_for_reducing_graph_partitions
        ):
            self.nodes = self.maybe_reorder_for_minimizing_partition(self.nodes)
            self.nodes = self.reorder_for_partition_with_simple_dependency(self.nodes)

        self.compute_last_usage()

        if torch._inductor.config.test_configs.track_memory_lifecycle:
            self.insert_memory_check_nodes()

        log_ir_post_fusion(self.nodes)
        # pyrefly: ignore[unbound-name]
        V.debug.graph_diagram(self.nodes)
        self.debug_draw_graph()

        # used during codegen:
        self.buffer_names_to_free: OrderedSet[str] = OrderedSet()

        # fx graph node to the position it appears in the graph
        # for debug attribution
        self.origin_to_index: dict[torch.fx.Node, int] = {}

        # The only source of which stream context we are currently in during the codegen phase.
        self._current_stream_ctx: EnterCudaStreamContextLine | None = None

        get_metric_table("graph_stats").add_row(
            lambda: {
                "graph_id": self.post_grad_graph_id,
                "num_nodes_before_fusion": self.num_orig_nodes,
                "num_nodes_after_fusion": len(self.nodes),
            }
        )

        # Unlike V.graph.removed_buffers, the op recorded here is removed but
        # we still need the buffer (generated in alternative ways)
        self.removed_ops: OrderedSet[str] = OrderedSet()