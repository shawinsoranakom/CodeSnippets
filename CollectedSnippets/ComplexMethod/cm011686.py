def _add_first_outputs(
        self,
        outputs: OutputType,
        static_input_persistent_storage_ptrs: dict[int, StorageWeakRefWrapper],
    ) -> None:
        "Add the outputs from the first invocation of the node and set up metadata"

        # getting liveness before we have added the outputs to path, so the length
        # of the two lists is equal
        prev_liveness = self.recorded_liveness_before_graph
        curr_liveness = self._get_liveness(self.path_weakrefs)

        delta = self._get_different_indices(prev_liveness, curr_liveness)
        self.expected_dead_indices_after_graph = delta

        assert len(self.outputs_weakrefs) == 0
        # index from data pointer to index in outputs
        output_new_storages_index: dict[StorageDataPtr, int] = {}

        self.unaliased_in_all_paths = [False for _ in range(len(outputs))]
        self.static_output_tensors = [None for _ in range(len(outputs))]

        for i, o in enumerate(outputs):
            if o is None or not isinstance(o, torch.Tensor):
                self.output_storage_alias.append(UnaliasedStorage)
                continue

            torch._check(
                o.is_cuda or o.untyped_storage().data_ptr() == 0,
                lambda: (
                    "Expected all cuda outputs in cuda graph recording. Non cuda output "
                    f"from {self.stack_traces[i] if self.stack_traces else '(unknown)'}"
                ),
            )

            ref = static_input_persistent_storage_ptrs.get(
                o.untyped_storage().data_ptr()
            )
            # also treat empty storages as static outputs because we do not need to manage their lifetime
            # and they should not participate in checkpointing
            is_empty_storage = o.untyped_storage().data_ptr() == 0
            if (ref and ref() is not None) or is_empty_storage:
                self.output_storage_alias.append(None)
                self.static_output_tensors[i] = o
                continue

            path_ref = self._is_alias_of_live_recorded_tensor(o)
            if path_ref is not None:
                self._mark_prior_graph_output_as_aliased(path_ref)

                for idx, inp_path_ref in enumerate(
                    self.live_cudagraph_managed_path_refs
                ):
                    if path_ref == inp_path_ref:
                        self.preserved_aliased_inputs[idx] = True
                self.output_storage_alias.append(AliasesPriorGraphOutput(path_ref))
                continue

            if o.untyped_storage().data_ptr() in output_new_storages_index:
                index = output_new_storages_index[o.untyped_storage().data_ptr()]
                self.unaliased_in_all_paths[index] = False
                self.output_storage_alias.append(AliasesNewOutput(index))
                continue

            output_new_storages_index[o.untyped_storage().data_ptr()] = i
            self.output_storage_alias.append(UnaliasedStorage)
            self.unaliased_in_all_paths[i] = True

        if self.stack_traces is None:
            self.stack_traces = [None for _ in range(len(outputs))]
        else:
            assert len(self.stack_traces) == len(outputs), (
                "Wrong number of stack traces passed in"
            )

        assert not self.outputs_weakrefs
        for out, static_output_tensor in zip(outputs, self.static_output_tensors):
            if not isinstance(out, torch.Tensor) or static_output_tensor is not None:
                self.outputs_weakrefs.append(None)
                self.tensor_weakrefs.append(None)
            else:
                self.outputs_weakrefs.append(StorageWeakRefWrapper(out))
                self.tensor_weakrefs.append(TensorWeakRef(out))

        self.recorded_liveness_after_graph = self._get_liveness(self.path_weakrefs)
        self.checkpointed_caching_state = torch._C._cuda_getCheckpointState(
            self.device, self.cuda_graphs_pool
        )

        # now, get liveness with outputs added
        for depth in range(len(self.path_weakrefs)):
            for output_index in range(len(self.path_weakrefs[depth])):
                if is_live(self.path_weakrefs[depth][output_index]):
                    self.live_indices_after_graph.append((depth, output_index))

        self.debug_check_invariants_after_invocation()
        if config.triton.slow_path_cudagraph_asserts:
            check_memory_pool(
                self.device, self.cuda_graphs_pool, list(self.path_live_weakrefs())
            )