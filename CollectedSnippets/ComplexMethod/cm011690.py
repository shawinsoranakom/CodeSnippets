def dealloc_current_path_weakrefs(self) -> None:
        assert self.current_node is not None
        # TODO: we could also allow the these weak refs to continue to be allocated,
        # but that adds some complications.

        stor_stack_trace: dict[int, str | None] = {}
        for node in self.current_node._path_from_root:
            assert node.stack_traces is not None
            assert len(node.tensor_weakrefs) == len(node.stack_traces)
            for t, stack_trace in zip(node.tensor_weakrefs, node.stack_traces):
                ten = None if t is None else t()
                if ten is None:
                    continue

                torch._C._set_storage_access_error_msg(
                    ten, self.format_dealloc_msg(stack_trace)
                )

            # we would to enable the following assertion, but an internal model failed with a command
            # that does not repro. len(node.outputs_weakrefs) == len(node.stack_traces)
            # so, pessimistically assume that they might differ by doing the debug info
            # loop separately from the dealloc loop
            if self.disable_invalidate_aliases:
                continue

            for storage_ref, stack_trace in zip(
                node.outputs_weakrefs, node.stack_traces
            ):
                if not storage_ref:
                    continue

                stor_stack_trace[storage_ref.data_ptr()] = stack_trace

        deleted = OrderedSet[Any]()
        for storage_ref in self.current_node.path_live_weakrefs():
            _storage_deref = storage_ref()
            if _storage_deref and storage_ref.data_ptr() not in deleted:
                deleted.add(storage_ref.data_ptr())

                msg = self.format_dealloc_msg(
                    stor_stack_trace.get(storage_ref.data_ptr())
                )
                torch._C._free_And_Remove_DeleterFn(_storage_deref)

                if self.disable_invalidate_aliases:
                    continue

                torch._C._set_storage_data_ptr_access_error_msg(_storage_deref, msg)