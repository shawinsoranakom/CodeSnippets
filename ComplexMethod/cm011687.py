def debug_assert_invariants(
        self, expected_liveness: list[list[bool]], newly_dead: list[PathOutputIndex]
    ) -> None:
        if not config.triton.fast_path_cudagraph_asserts:
            return

        for i, node in enumerate(self._path_from_root):
            assert self.path_weakrefs[i] is node.outputs_weakrefs

        nodes = list(self._path_from_root)

        live_blocks = get_block_addrs(self.cuda_graphs_pool)

        live_storage_data_ptrs = OrderedSet[Any]()
        live_storage_weak_ptrs = OrderedSet[Any]()

        for depth, outputs_liveness in enumerate(expected_liveness):
            for output_idx, output_liveness in enumerate(outputs_liveness):
                # tensor can die early, but it can't be alive when it should be dead
                w = self.path_weakrefs[depth][output_idx]
                if (stor_weak_ptr_and_data_ptr := maybe_deref(w)) is not None:
                    assert output_liveness
                    stor_weak_ptr, stor_data_ptr = stor_weak_ptr_and_data_ptr
                    assert (stor_data_ptr in live_storage_data_ptrs) == (
                        stor_weak_ptr in live_storage_weak_ptrs
                    )
                    live_storage_data_ptrs.add(stor_data_ptr)
                    live_storage_weak_ptrs.add(stor_weak_ptr)

                    is_persistent_alias = (
                        nodes[depth].static_output_tensors[output_idx] is not None
                    )

                    if is_persistent_alias:
                        assert stor_data_ptr not in live_blocks

        for depth, output_index in newly_dead:
            assert not is_live(self.path_weakrefs[depth][output_index])