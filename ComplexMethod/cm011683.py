def __init__(
        self,
        wrapped_function: WrappedFunction,
        id: GraphID,
        parent: CUDAGraphNode | None,
        inputs: list[InputType],
        cuda_graphs_pool: _POOL_HANDLE,
        device_index: int,
        stack_traces: StackTraces | None,
        stream: torch.cuda.Stream,
        mode: CompilationMode | None,
        compile_id: CompileId | None,
    ) -> None:
        assert isinstance(inputs, (list, tuple))

        self.wrapped_function = wrapped_function
        self.id = id
        self.device = device_index
        self.stack_traces = stack_traces
        self.stream = stream

        # Enable re-record a cudagraph when static tensor address changed.
        # if not we should error when it changed.
        self.rerecord_if_static_inputs_change = True

        # if this is a root parent will be None. use weakref to prevent reference cycle
        self._parent = weakref.ref(parent) if parent is not None else None
        # reference to the shared memory pool for the entire cuda graphs tree
        self.cuda_graphs_pool = cuda_graphs_pool

        # A single wrapped function may be recorded multiple times if memory patterns or
        # invariants change from one execution to the next
        self.children: dict[FunctionID, list[CUDAGraphNode]] = defaultdict(list)

        # StorageWeakRef maintains whether the Storage C++ object remains allocated,
        # not whether the corresponding memory has been deallocated. In order
        # to use them to track memory deallocations we must maintain a single StorageWeakRef
        # for all Storages that reference that memory (even if we are constructing Storages
        # that do not have a deallocator function). We maintain one single storage_cache
        # as we execute any tree path. When we retrieve a storage from the cache we
        # check that it is still alive, and we hash based on observed recording data ptr
        # and storage cdata.

        # we preserve a single reference to executed outputs that is then referenced
        # in children to avoid children having to chase parent pointers in the hot path
        # DO NOT reassign output_weakrefs, only call `clear()`
        # Path is a series of nodes from root to the current node
        self.outputs_weakrefs: OutputList[StorageWeakRefWrapper | None] = []
        self.path_weakrefs: LevelList[OutputList[StorageWeakRefWrapper | None]] = [
            node.outputs_weakrefs for node in self._path_from_root
        ]
        self.path_stacktraces: LevelList[StackTraces | None] = [
            node.stack_traces for node in self._path_from_root
        ]
        self.tensor_weakrefs: OutputList[TensorWeakRef | None] = []

        # tensors which are outputs of previous graphs in the tree
        self.cudagraph_managed_idxs: list[int] = [
            idx
            for idx, t in enumerate(inputs)
            if isinstance(t, torch.Tensor) and self._is_cuda_graph_recorded_tensor(t)
        ]

        # (depth, offset) of live tensors which are alias of previous graph outputs
        self.live_cudagraph_managed_path_refs: InputList[PathOutputIndex | None] = [
            (
                self._is_alias_of_live_recorded_tensor(t)
                if isinstance(t, torch.Tensor)
                else None
            )
            for t in inputs
        ]

        # when replay, preserve the liveness of an input if it AliasesPriorGraphOutput
        # and also aliases an output of the current CUDAGraphNode
        self.preserved_aliased_inputs: InputList[bool] = [False] * len(inputs)

        # Opaque values (e.g. DeviceMesh, ProcessGroup) are non-tensor
        # inputs that cannot be copied like tensors. We include them in
        # static_input_idxs to keep them out of non_static_input_idx
        # (which drives the tensor-copy path during replay). "Static"
        # here just means "don't try to copy this as a tensor" — it
        # does NOT mean the object is semantically immutable.
        #
        # Opaque indices must also be excluded from any list passed to
        # _tensors_data_ptrs_at_indices_equal (the C++ data-pointer
        # stability check), because opaque objects have no data_ptr.
        # That is why tensor_static_input_idxs and
        # non_managed_static_input_idxs filter them out below.
        opaque_input_idxs = OrderedSet(
            i for i, inp in enumerate(inputs) if is_opaque_value(inp)
        )
        static_input_idxs = OrderedSet(wrapped_function.static_input_idxs)
        cudagraph_managed_idxs = OrderedSet(self.cudagraph_managed_idxs)

        self.static_input_idxs: list[int] = list(
            static_input_idxs | cudagraph_managed_idxs | opaque_input_idxs
        )

        self.non_static_input_idx: LevelList[int] = [
            i for i in range(len(inputs)) if i not in self.static_input_idxs
        ]

        counters["inductor"]["cudagraph_recorded_non_static_inputs"] += len(
            self.non_static_input_idx
        )

        self.non_managed_static_input_idxs: LevelList[int] = LevelList(
            static_input_idxs - cudagraph_managed_idxs - opaque_input_idxs
        )

        self.tensor_static_input_idxs: list[int] = list(
            static_input_idxs | cudagraph_managed_idxs
        )

        def maybe_get_static_data_ptr(
            idx: int,
            inputs: list[InputType],
            static_input_idxs: list[int],
        ) -> int | None:
            inp = inputs[idx]
            if isinstance(inp, torch.Tensor) and idx in static_input_idxs:
                return inp.data_ptr()
            return None

        self.static_input_data_ptrs: InputList[int | None] = [
            maybe_get_static_data_ptr(i, inputs, self.static_input_idxs)
            for i in range(len(inputs))
        ]

        # When we checkpoint, and free generations, we will be manually freeing the outputs
        # of CUDAGraphNodes. We should not be freeing parameters, not do we need to account for
        # their liveness (they are static), so we need to compute which outputs are aliases of
        # parameters. Some static inputs are saved tensors from the forward that die in the backward.
        # Their locations are static but lifetimes are not. We only include the persistent static
        # data ptrs below because the non persistent data ptrs may be outputs of this record and
        # fresh allocations.

        # precompute expanded dims to avoid computing in the hot path
        self.expanded_dims: list[list[int]] = [
            get_expanded_dims(x)
            if isinstance(x, torch.Tensor) and idx not in self.static_input_idxs
            else []
            for idx, x in enumerate(inputs)
        ]

        # For each node in path, which outputs were observed to be live
        # before invoking graph recording, and after graph recording
        self.recorded_liveness_before_graph: LevelList[OutputList[bool]] = []
        self.recorded_liveness_after_graph: LevelList[OutputList[bool]] = []

        # List of tuples of (depth, output_index) that index into node at depth
        # number of nodes from root and output_index of outputs. Will index into
        # path_weakrefs.
        self.expected_dead_indices_before_graph: list[PathOutputIndex] = []
        self.expected_dead_indices_after_graph: list[PathOutputIndex] = []

        # all live indices after graph recording
        self.live_indices_after_graph: list[PathOutputIndex] = []

        if self.parent is not None:
            previous_liveness = self.parent.recorded_liveness_after_graph
            curr_liveness = self._get_liveness(self.path_weakrefs)

            different_indices = self._get_different_indices(
                previous_liveness, curr_liveness
            )

            self.recorded_liveness_before_graph = curr_liveness
            self.expected_dead_indices_before_graph = different_indices

        rng_states = [inp for inp in inputs if isinstance(inp, torch.Generator)]

        recording_inputs = self._allocate_and_copy_recording_inputs(inputs)
        # recording inputs will copy over memory, so we can free non recording inputs

        inputs.clear()
        del inputs

        # graph used for recording model invocation
        self.graph: torch.cuda.CUDAGraph | None = torch.cuda.CUDAGraph()

        # TODO: register_generator_state should potentially take explicit device
        with torch.cuda.device(self.device):
            for rng_state in rng_states:
                self.graph.register_generator_state(rng_state)

        # we allocate non-static inputs within the same memory pool as the CUDAGraph
        # which we will record the model with. For memory efficiency, it is important
        # to reclaim the input memory when the inputs are no longer live. To accomplish this,
        # we reconstruct tensors at the correct data pointers of our inputs which are
        # non owning and do not prevent deallocation. On subsequent executions, input values
        # will be copied over to these tensors.
        self.reconstructed_inputs: list[InputType] = [
            self._reconstruct_from_tensor_metadata(self._tensor_metadata(x))
            if isinstance(x, torch.Tensor)
            else x
            for x in recording_inputs
        ]

        # DO THE RECORDING!!!
        # We record the CUDA graph in the constructor of CUDAGraphNode, which
        # gives you what the CPU side compute of the function would do.  We
        # don't throw the recording outputs away: their memory is
        # correctly accounted for in the CUDAGraphs caching allocator.  This
        # means on the very FIRST run of the CUDA graph node, we can directly
        # do more recording, because we have a valid caching allocator state.
        # NB: This relies on run() being called immediately after the
        # constructor, otherwise this optimization would not be valid.

        # initialized below in _record

        self.checkpointed_caching_state: AllocatorState | None = None

        # Output Storage Alias information, can be:
        # - A new, unaliased storage, or the output is None
        # - An alias of an output of a prior graph
        # - An alias of an output already created in the reconstructed outputs
        # This is None if the output in question is an int
        self.output_storage_alias: OutputList[OutputAliasInfo | None] = []

        # is the output Storage unaliased in subsequent outputs, of all subsequent paths
        # if it is, we cached the output tensor and adjust storage liveness tracking to also
        # check if the output tensor does not have an additional python reference.
        # If a descendent node discovers it has an alias of a prior output, then the output
        # will no longer be cached in the ancestor.
        # The large majority of tensors are unaliased, and preserving aliased output tensors would add
        # significant additional complexity with marginal gains
        # The cached tensor outputs are added on the first execution, and cleared whenever we need
        # to do subsequent recording
        self.unaliased_in_all_paths: OutputList[bool] = []
        self.cached_tensor_outputs: OutputList[Tensor | None] = []

        # if an output aliases a static, persistent input then the corresponding Tensor will
        # be set here. These are different than cached tensors, because they are tensors that
        # are aliases of parameters that are always live.
        self.static_output_tensors: OutputList[Tensor | None] = []

        # Cleared after recording
        with dynamo_timed_cudagraph("CUDAGraphNode.record", compile_id, mode):
            self.recording_outputs: OutputType | None = self._record(
                wrapped_function.model, recording_inputs
            )
        self.outputs_metadata: OutputList[dict[str, Any] | int | None] = []

        # As with inputs, we do not want to keep the outputs permanently alive because that would prevent
        # their memory being reclaimed in subsequent cuda graph recordings. We record the tensor metadata
        # needed to reconstruct instead.
        assert self.recording_outputs is not None
        for out in self.recording_outputs:
            if isinstance(out, torch.Tensor):
                self.outputs_metadata.append(
                    self._tensor_metadata(out, ignore_storage_offset=False)
                )
            else:
                assert isinstance(out, (int, type(None))), type(out)
                self.outputs_metadata.append(out)

        self.graph.replay()