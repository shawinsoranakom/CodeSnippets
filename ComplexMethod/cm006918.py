def __init__(self, **kwargs) -> None:
        # Initialize instance-specific attributes first
        if overlap := self._there_is_overlap_in_inputs_and_outputs():
            msg = f"Inputs and outputs have overlapping names: {overlap}"
            raise ValueError(msg)
        self._output_logs: dict[str, list[Log]] = {}
        self._current_output: str = ""
        self._metadata: dict = {}
        self._ctx: dict = {}
        self._code: str | None = None
        self._logs: list[Log] = []

        # Initialize component-specific collections
        self._inputs: dict[str, InputTypes] = {}
        self._outputs_map: dict[str, Output] = {}
        self._results: dict[str, Any] = {}
        self._attributes: dict[str, Any] = {}
        self._edges: list[EdgeData] = []
        self._components: list[Component] = []
        self._event_manager: EventManager | None = None
        self._token_usage: Usage | None = None
        self._state_model = None
        self._telemetry_input_values: dict[str, Any] | None = None

        # Process input kwargs
        inputs = {}
        config = {}
        for key, value in kwargs.items():
            if key.startswith("_"):
                config[key] = value
            elif key in CONFIG_ATTRIBUTES:
                config[key[1:]] = value
            else:
                inputs[key] = value

        self._parameters = inputs or {}
        self.set_attributes(self._parameters)

        # Store original inputs and config for reference
        self.__inputs = inputs
        self.__config = config or {}

        # Add unique ID if not provided
        if "_id" not in self.__config:
            self.__config |= {"_id": f"{self.__class__.__name__}-{nanoid.generate(size=5)}"}

        # Initialize base class
        super().__init__(**self.__config)

        # Post-initialization setup
        if hasattr(self, "_trace_type"):
            self.trace_type = self._trace_type
        if not hasattr(self, "trace_type"):
            self.trace_type = "chain"

        # Setup inputs and outputs
        self.reset_all_output_values()
        if self.inputs is not None:
            self.map_inputs(self.inputs)
        self.map_outputs()

        # Final setup
        self._set_output_types(list(self._outputs_map.values()))
        self.set_class_code()