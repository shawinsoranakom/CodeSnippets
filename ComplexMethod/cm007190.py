def __init__(
        self,
        data: NodeData,
        graph: Graph,
        *,
        base_type: str | None = None,
        is_task: bool = False,
        params: dict | None = None,
    ) -> None:
        # is_external means that the Vertex send or receives data from
        # an external source (e.g the chat)
        self._lock: asyncio.Lock | None = None
        self.will_stream = False
        self.updated_raw_params = False
        self.id: str = data["id"]
        self.base_name = self.id.split("-")[0]
        self.is_state = False
        # TODO: This won't be enough in the long term
        # we need to have a better way to determine if a vertex is an input or an output
        type_strings = [self.id.split("-")[0], data["data"]["type"]]
        self.is_input = any(input_component_name in type_strings for input_component_name in INPUT_COMPONENTS)
        self.is_output = any(output_component_name in type_strings for output_component_name in OUTPUT_COMPONENTS)
        self._is_loop = None
        self.has_session_id = None
        self.custom_component = None
        self.has_external_input = False
        self.has_external_output = False
        self.graph = graph
        self.full_data = data.copy()
        self.base_type: str | None = base_type
        self.outputs: list[dict] = []
        self.parse_data()
        self.built_object: Any = UnbuiltObject()
        self.built_result: Any = None
        self.built = False
        self._successors_ids: list[str] | None = None
        self.artifacts: dict[str, Any] = {}
        self.artifacts_raw: dict[str, Any] | None = {}
        self.artifacts_type: dict[str, str] = {}
        self.steps: list[Callable] = [self._build]
        self.steps_ran: list[Callable] = []
        self.task_id: str | None = None
        self.is_task = is_task
        self.params = params or {}
        self.parent_node_id: str | None = self.full_data.get("parent_node_id")
        self.load_from_db_fields: list[str] = []
        self.parent_is_top_level = False
        self.layer = None
        self.result: ResultData | None = None
        self.results: dict[str, Any] = {}
        self.outputs_logs: dict[str, OutputValue] = {}
        self.logs: dict[str, list[Log]] = {}
        self.has_cycle_edges = False
        try:
            self.is_interface_component = self.vertex_type in InterfaceComponentTypes
        except ValueError:
            self.is_interface_component = False

        self.use_result = False
        self.build_times: list[float] = []
        self.state = VertexStates.ACTIVE
        self.output_names: list[str] = [
            output["name"] for output in self.outputs if isinstance(output, dict) and "name" in output
        ]
        self._incoming_edges: list[CycleEdge] | None = None
        self._outgoing_edges: list[CycleEdge] | None = None