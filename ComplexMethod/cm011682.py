def run(self, new_inputs: Any) -> OutputType:
        assert not self.has_run, "Wrapped function should never be run twice"

        # See: output_is_alias_of_persistent_static_inputs below. We should only be returning freshly created
        # storages in path_live_weakrefs.
        existing_path_data_ptrs = OrderedSet(
            [t.data_ptr() for t in self.path_live_weakrefs() if t()]
        )

        def get_non_cudagraph_inps() -> list[weakref.ReferenceType[UntypedStorage]]:
            non_cudagraph_inps = [
                weakref.ref(t.untyped_storage())
                for t in itertools.chain(new_inputs, self.wrapped_function.constants)
                if isinstance(t, torch.Tensor)
                and t.untyped_storage().data_ptr() not in existing_path_data_ptrs
            ]
            return non_cudagraph_inps

        non_cudagraph_inps_storages = get_non_cudagraph_inps()

        if config.triton.slow_path_cudagraph_asserts and not self.already_warm:
            refs = list(self.path_live_weakrefs())
            check_memory_pool(self.device_index, self.cuda_graphs_pool, refs)

        with (
            torch.cuda.device(self.device_index),
            disable_conv_cache_emptying(),
            clear_cublas_manager(),
            _use_cuda_memory_pool_manager(
                self.device_index, self.cuda_graphs_pool, self.stream
            ),
            # NB: must go after _use_cuda_memory_pool_manager which switches the stream
            _update_current_stream_external_object(),
            ControlFlowOpWarmupDispatchMode(),
            get_history_recording(),
        ):
            out = self.wrapped_function.model(new_inputs)

        # We need to know which outputs are allocated within the cudagraph pool
        # so that we can deallocate them at the beginning of the next cudagraph step,
        # and set their access to error.
        # We use a weakref to the inputs storage, in case a block which was previously
        # allocated to the general caching allocator pool gets reallocated to a private pool.

        non_cudagraph_inps_storage_ptrs = OrderedSet[Any]()
        for storage in non_cudagraph_inps_storages:
            s = storage()
            if s is not None:
                non_cudagraph_inps_storage_ptrs.add(s._cdata)

        assert len(new_inputs) == 0

        # sdpa returns cpu tensors when not recording cuda graph
        def add_ref(o: Any) -> bool:
            return (
                isinstance(o, torch.Tensor)
                and o.is_cuda
                and o.untyped_storage()._cdata not in non_cudagraph_inps_storage_ptrs
                and o.untyped_storage().data_ptr() != 0
            )

        self.outputs_weakrefs.extend(
            [map_to_ref(o) if add_ref(o) else None for o in out]
        )
        self.tensor_weakrefs.extend(
            [TensorWeakRef(o) if add_ref(o) else None for o in out]
        )

        if config.triton.slow_path_cudagraph_asserts and not self.already_warm:
            out_refs = list(self.path_live_weakrefs())
            check_memory_pool(self.device_index, self.cuda_graphs_pool, out_refs)

        return out