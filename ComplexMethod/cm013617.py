def __init__(
        self,
        module: torch.fx.GraphModule,
        sample_input: Tensors,
        compare_fn: Callable[
            [TensorOrTensors, TensorOrTensors, Names], tuple[float, bool]
        ],
        settings: _MinimizerSettingBase,
        module_exporter: Callable[[Tensors, torch.fx.GraphModule, str], None]
        | None = None,
        exclusion_fn: Callable[[NodeList, int, int], None] | None = None,
    ) -> None:
        if not isinstance(module, torch.fx.GraphModule):
            raise AssertionError(f"Expected GraphModule, got {type(module)}")

        self.module = module
        self.sample_input = sample_input
        self.compare_fn = compare_fn
        self.module_exporter = module_exporter
        self.settings = settings
        self.exclusion_fn = exclusion_fn

        # Stores outputs of run_a function
        self.a_outputs: dict[str, Any] = {}

        # Stores outputs of run_b function
        self.b_outputs: dict[str, Any] = {}

        # Stores the results of compare_fn
        self.results: dict[Any, Any] = {}

        # Stores the report for the runs
        self.reports: list[list[str]] = []

        # Current iteration
        self.iteration: int = 0

        callable_nodes = {
            node for node in self.module.graph.nodes if node.op in CALLABLE_NODE_OPS
        }
        self.run_shape_prop()
        self.fusions = FxNetAccFusionsFinder(self.module, callable_nodes)()

        # Check if number of input in sample_input matches the number of placeholders
        placeholders = [
            node.name for node in self.module.graph.nodes if node.op == "placeholder"
        ]
        if len(placeholders) != len(self.sample_input):
            raise AssertionError(
                f"Placeholder count ({len(placeholders)}) does not match "
                f"sample_input count ({len(self.sample_input)})"
            )

        # Store sample_input
        for i, name in enumerate(placeholders):
            self.a_outputs[name] = sample_input[i]
            self.b_outputs[name] = sample_input[i]