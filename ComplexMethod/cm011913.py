def _compute_fusion_metadata(
        self, scheduling, epilogue_nodes, prologue_nodes, buf_name_to_prologue_group
    ):
        """Compute fusion metadata for external backends.

        Determines eligible epilogues/prologues, builds epilogue specs,
        and computes prologue sources — all before render().

        Hook setup (_setup_epilogue_hook / _setup_prologue_hook) cannot
        happen here because it requires V.kernel context, which is only
        active during codegen_template_body → render().
        """
        self._scheduling_ref = scheduling
        from torch._inductor.dependencies import MemoryDep

        tb = self._template_buffer
        self._eligible_epilogues = self._find_eligible_epilogues(
            epilogue_nodes, tb.epilogue_fusable_outputs
        )
        self._epilogue_nodes_by_subgraph = defaultdict(
            list,
            {i: [sn] for i, (sn, _, _, _) in enumerate(self._eligible_epilogues)},
        )
        fused_ids = OrderedSet(id(sn) for sn, _, _, _ in self._eligible_epilogues)
        self._unfused_epilogues = [
            n
            for n in epilogue_nodes
            if id(n) not in fused_ids and not isinstance(n.node, ir.MultiOutput)
        ]
        self._prologue_sources = {
            buf_name: frozenset(
                d.name for d in pro_node.read_writes.reads if isinstance(d, MemoryDep)
            )
            for buf_name, pro_nodes in buf_name_to_prologue_group.items()
            for pro_node in pro_nodes
        }

        # Build simplified epilogue interface: _epilogue_idx_by_param,
        # _epilogue_keep_store, and _extra_store_targets.
        from torch._inductor.codegen.common import RemovedArg

        scheduler = V.graph.scheduler
        epilogues = self._eligible_epilogues

        # Compute fused node names for buffer removability
        fused_node_names = None
        if scheduler is not None:
            all_store_names = OrderedSet([tb.get_name()])
            all_store_names.update(tb._multi_output_children)
            all_store_names.update(st for _, _, _, st in epilogues if st)
            fused_node_names = OrderedSet(
                scheduler.name_to_buf[n].defining_op_name()
                for n in all_store_names
                if n in scheduler.name_to_buf
            )

        # Pre-register store_target buffers so we know their param names
        for _, _, _, store_target in epilogues:
            if (
                store_target is not None
                and store_target not in self.args.output_buffers
            ):
                self.args.output(store_target)

        # Build per-epilogue metadata
        for i, (_, output_buf, output_param, store_target) in enumerate(epilogues):
            self._epilogue_idx_by_param[output_param] = i

            can_remove = (
                store_target is not None
                and fused_node_names is not None
                and scheduler.can_buffer_be_removed_through_fusion(
                    output_buf, fused_node_names
                )
            )

            store_target_param_raw = (
                self.args.output_buffers.get(store_target)
                if store_target is not None
                else None
            )
            store_target_param = (
                None
                if isinstance(store_target_param_raw, RemovedArg)
                else store_target_param_raw
            )

            if store_target_param is not None:
                self._extra_store_targets[store_target] = store_target_param
                if can_remove:
                    self.removed_buffers.add(output_buf)
                else:
                    self._epilogue_keep_store.add(output_param)