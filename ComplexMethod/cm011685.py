def _record(self, model: ModelType, inputs: list[InputType]) -> OutputType:
        "Record the model"
        assert self.graph is not None

        def static_input_iter() -> Generator[torch.Tensor, None, None]:
            for i in self.wrapped_function.static_input_idxs:
                _inp = inputs[i]
                if isinstance(
                    _inp, torch.Tensor
                ) and not self._is_cuda_graph_recorded_tensor(_inp):
                    yield _inp

        # see: output_is_alias_of_persistent_static_inputs above
        static_input_persistent_storage_ptrs: dict[int, StorageWeakRefWrapper] = {
            inp.untyped_storage().data_ptr(): StorageWeakRefWrapper(inp)
            for inp in itertools.chain(
                static_input_iter(), self.wrapped_function.constants
            )
        }

        if config.triton.slow_path_cudagraph_asserts:
            # need to use parent live weakrefs because live_indices isn't set yet
            memory = (
                [] if self.parent is None else list(self.parent.path_live_weakrefs())
            )
            memory += [
                StorageWeakRefWrapper(elem)
                for i, elem in enumerate(inputs)
                if isinstance(elem, torch.Tensor)
                and i not in self.wrapped_function.static_input_idxs
                and elem.untyped_storage().data_ptr() != 0
            ]
            check_memory_pool(self.device, self.cuda_graphs_pool, memory)

        with (
            preserve_rng_state(),
            torch.cuda.device(self.device),
            clear_cublas_manager(),
            torch.cuda.graph(
                self.graph,
                stream=self.stream,
                pool=self.cuda_graphs_pool,
                capture_error_mode="thread_local",
            ),
            # NB: must go after torch.cuda.graph which switches the stream
            _update_current_stream_external_object(),
            CUDAGraphCaptureControlFlowOpDispatchMode(),
            get_history_recording(),
        ):
            static_outputs = model(inputs)

        # running model should reclaim memory
        assert len(inputs) == 0

        if not isinstance(static_outputs, (list, tuple)):
            static_outputs = (static_outputs,)

        # pyrefly: ignore [bad-argument-type]
        self._add_first_outputs(static_outputs, static_input_persistent_storage_ptrs)

        # pyrefly: ignore [bad-return]
        return static_outputs