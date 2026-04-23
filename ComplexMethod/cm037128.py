def __init__(
        self,
        graph: fx.GraphModule | None,
        vllm_config: VllmConfig,
        piecewise_compile_index: int,
        total_piecewise_compiles: int,
        sym_shape_indices: list[int],
        vllm_backend: VllmBackend,
        returns_tuple: bool,
        compiled_runnables: dict[str, Callable[..., Any]] | None = None,
        submod_name: str = "",
    ):
        """
        The backend for piecewise compilation.
        It mainly handles the compilation of static shapes and
        dispatching based on runtime shape.

        We will compile `self.graph` once for the general shape,
        and then compile for different shapes specified in
        `compilation_config.compile_sizes`.

        This class supports two mutually exclusive modes:
        1. Compilation (graph is set, compiled_runnables is None):
           Used during initial compilation when we have the FX graph
           and need to compile it for each shape range.
        2. Precompilation (graph is None, compiled_runnables is set):
           Used when loading from cache/AOT artifacts where we already
           have pre-compiled callables and don't need the original graph.

        Exactly one of graph or compiled_runnables must be provided.
        """
        assert bool(graph is not None) ^ bool(compiled_runnables is not None), (
            "exactly one of graph and compiled_runnables should be set."
        )

        self.graph = graph
        self.vllm_config = vllm_config
        self.compilation_config = vllm_config.compilation_config
        self.piecewise_compile_index = piecewise_compile_index
        self.total_piecewise_compiles = total_piecewise_compiles
        self.vllm_backend = vllm_backend
        self.compiled_runnables = compiled_runnables
        self.submod_name = submod_name

        self.is_first_graph = piecewise_compile_index == 0
        self.is_last_graph = piecewise_compile_index == total_piecewise_compiles - 1

        self.is_full_graph = total_piecewise_compiles == 1
        self.is_encoder_compilation = vllm_backend.is_encoder

        self.compile_ranges = self.compilation_config.get_compile_ranges()
        if self.is_encoder_compilation:
            # For encoder compilation we use the max int32 value
            # to set the upper bound of the compile ranges
            max_int32 = 2**31 - 1
            last_compile_range = self.compile_ranges[-1]
            assert (
                last_compile_range.end
                == vllm_config.scheduler_config.max_num_batched_tokens
            )
            self.compile_ranges[-1] = Range(
                start=last_compile_range.start, end=max_int32
            )

        log_string = f"PiecewiseBackend: compile_ranges: {self.compile_ranges}"
        logger.debug_once(log_string)

        self.compile_sizes = self.compilation_config.compile_sizes
        log_string = f"PiecewiseBackend: compile_sizes: {self.compile_sizes}"
        logger.debug_once(log_string)

        self.sym_shape_indices = sym_shape_indices
        self.returns_tuple = returns_tuple

        # the entries for ranges that we need to either
        self.range_entries: dict[Range, RangeEntry] = {}

        # We only keep compilation management inside this class directly.
        if self.compile_sizes is not None:
            for size in self.compile_sizes:
                if isinstance(size, str):
                    assert size == "cudagraph_capture_sizes"
                    raise NotImplementedError(
                        "cudagraph_capture_sizes not supported in compile_sizes."
                        "This should be handled in `post_init_cudagraph_sizes`."
                    )
                else:
                    assert isinstance(size, int)
                    range = Range(start=size, end=size)
                    if range not in self.compile_ranges:
                        self.range_entries[range] = RangeEntry(
                            compile_range=range,
                        )

        for range in self.compile_ranges:
            self.range_entries[range] = RangeEntry(
                compile_range=range,
            )

        # Track whether we've logged the graph for this subgraph (only log once)
        self._graph_logged = False

        if self.graph is not None:
            self.compile_all_ranges()
        else:
            self.load_all_ranges()