def apply_checkpoint_execution_state_in_allocator(self) -> None:
        """
        Checkpoint the current execution state in the caching allocator so that
        additional cudagraph recordings can be made respecting existent live storages.
        """
        assert isinstance(self.current_node, CUDAGraphNode)
        self.debug_checkpointing_counter += 1
        log.debug(
            "Checkpointing cuda caching allocator state. Number of checkpoints %d",
            self.debug_checkpointing_counter,
        )

        state = self.current_node.checkpointed_caching_state
        device = self.current_node.device
        assert state is not None and device is not None

        # currently we deallocate on instead of allowing stale recordings
        stale_storages: list[int] = []

        # remove cached tensors, otherwise they would prevent memory from being
        # reclaimed in subsequent recordings
        self.current_node.remove_path_cached_tensors()
        live_storages_wrappers = list(self.current_node.path_live_weakrefs())

        # path_live_weakrefs guarantees that t() will not be None
        live_storages_weak_refs: list[int] = [t() for t in live_storages_wrappers]  # type: ignore[misc]
        ptrs_to_deallocate = self.current_node.data_ptrs_dead_since_invocation()
        torch._C._cuda_setCheckpointPoolState(
            device,
            # pyrefly: ignore [bad-argument-type]
            state,
            stale_storages,
            live_storages_weak_refs,
        )

        # NB: deduplicate aliased outputs
        for ptr in OrderedSet(ptrs_to_deallocate):
            torch._C._cuda_cudaCachingAllocator_raw_delete(ptr)

        # Now the live blocks should be exactly equal to the live storages in private pool
        if config.triton.slow_path_cudagraph_asserts:
            check_memory_pool(
                self.device_index, self.cuda_graphs_thread_pool, live_storages_wrappers
            )
            for wrapper in live_storages_wrappers:
                storage_ptr = wrapper()
                assert storage_ptr is not None
                assert torch._C._has_Standard_Deleter(storage_ptr)
                assert wrapper.data_ptr() not in ptrs_to_deallocate