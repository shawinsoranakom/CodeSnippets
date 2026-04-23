def __init__(
        self,
        start: Component | None = None,
        end: Component | None = None,
        flow_id: str | None = None,
        flow_name: str | None = None,
        description: str | None = None,
        user_id: str | None = None,
        log_config: LogConfig | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initializes a new Graph instance.

        If both start and end components are provided, the graph is initialized and prepared for execution.
        If only one is provided, a ValueError is raised. The context must be a dictionary if specified,
        otherwise a TypeError is raised. Internal data structures for vertices, edges, state management,
        run management, and tracing are set up during initialization.
        """
        if log_config:
            configure(**log_config)

        self._start = start
        self._state_model = None
        self._end = end
        self._prepared = False
        self._runs = 0
        self._updates = 0
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.description = description
        self.user_id = user_id
        self._is_input_vertices: list[str] = []
        self._is_output_vertices: list[str] = []
        self._is_state_vertices: list[str] | None = None
        self.has_session_id_vertices: list[str] = []
        self._sorted_vertices_layers: list[list[str]] = []
        self._run_id = ""
        self._session_id = ""
        self._start_time = datetime.now(timezone.utc)
        self.inactivated_vertices: set = set()
        self.activated_vertices: list[str] = []
        self.vertices_layers: list[list[str]] = []
        self.vertices_to_run: set[str] = set()
        self.stop_vertex: str | None = None
        self.inactive_vertices: set = set()
        # Conditional routing system (separate from ACTIVE/INACTIVE cycle management)
        self.conditionally_excluded_vertices: set = set()  # Vertices excluded by conditional routing
        self.conditional_exclusion_sources: dict[str, set[str]] = {}  # Maps source vertex -> excluded vertices
        self.edges: list[CycleEdge] = []
        self.vertices: list[Vertex] = []
        self.run_manager = RunnableVerticesManager()
        self._vertices: list[NodeData] = []
        self._edges: list[EdgeData] = []

        self.top_level_vertices: list[str] = []
        self.vertex_map: dict[str, Vertex] = {}
        self.predecessor_map: dict[str, list[str]] = defaultdict(list)
        self.successor_map: dict[str, list[str]] = defaultdict(list)
        self.in_degree_map: dict[str, int] = defaultdict(int)
        self.parent_child_map: dict[str, list[str]] = defaultdict(list)
        self._run_queue: deque[str] = deque()
        self._first_layer: list[str] = []
        self._lock: asyncio.Lock | None = None
        self.raw_graph_data: GraphData = {"nodes": [], "edges": []}
        self._is_cyclic: bool | None = None
        self._cycles: list[tuple[str, str]] | None = None
        self._cycle_vertices: set[str] | None = None
        self._call_order: list[str] = []
        self._snapshots: list[dict[str, Any]] = []
        self._end_trace_tasks: set[asyncio.Task] = set()
        self._is_subgraph = False

        if context and not isinstance(context, dict):
            msg = "Context must be a dictionary"
            raise TypeError(msg)
        self._context = dotdict(context or {})
        # Lazy initialization - only get tracing service when needed
        self._tracing_service: TracingService | None = None
        self._tracing_service_initialized = False
        if start is not None and end is not None:
            self._set_start_and_end(start, end)
            self.prepare(start_component_id=start.get_id())
        if (start is not None and end is None) or (start is None and end is not None):
            msg = "You must provide both input and output components"
            raise ValueError(msg)