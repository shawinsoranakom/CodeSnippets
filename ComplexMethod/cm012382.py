def register_custom_op_autotuning(
    custom_op: torch._library.custom_ops.CustomOpDef | torch._ops.OpOverload,
    configs: list[CustomOpConfig] | list[Callable[..., Any]] | None = None,
    config_generator: Callable[[dict[str, torch.Tensor]], list[CustomOpConfig]]
    | None = None,
    name: str | None = None,
    input_gen_fns: dict[str, Callable[[torch.Tensor], torch.Tensor]] | None = None,
    dispatch_on: dict[str, Any] | None = None,
    split_points: list[int] | None = None,
    min_speedup_threshold: float = 1.0,
    benchmark_with_cudagraphs: bool = False,
) -> None:
    """Register custom op for autotuning with custom_op configs where each config
    specifies a decomposition implementation function with its parameter values.
    It also supports Range-based autotuning to benchmark per range and generate
    runtime dispatch.

    Args:
        custom_op: Custom operation (CustomOpDef from @torch.library.custom_op) or
                   OpOverload (e.g., torch.ops.aten.mm.default)
        configs: List of CustomOpConfig objects for static inputs. Mutually exclusive with config_generator.
        config_generator: Dynamic config generator function that takes a dict mapping
                          parameter names to fake tensors, and returns list[CustomOpConfig]
                          based on input tensor properties. Mutually exclusive with configs.
        name: Operation name (default: "{op_name}_autotuned")
        input_gen_fns: Custom input generators for benchmarking
        dispatch_on: Dict for range-based dispatch with keys:
            - 'tensor_name': Name of tensor parameter to dispatch on
            - 'dim': Dimension index to check size
            - 'unbounded_size' (optional): Benchmark size for the unbounded (last) range, such
                as [2048, inf] -> [2048, unbounded_size]. Set based on your expected workload size.
                Default is DEFAULT_RANGE_UPPER_BOUND=65536.
        split_points: List of range endpoints in ascending order for range-based autotuning
        min_speedup_threshold: Only pick a non-fallback choice if it beats the fallback
            by at least this ratio. Default is 1.0 (any speedup wins). Set to e.g. 1.1
            to require 10% speedup over fallback.
        benchmark_with_cudagraphs: If True, benchmark the fallback kernel using CUDA graph
            capture and replay for fair comparison with compiled kernels. Default is False.

    The default/fallback implementation is automatically derived:
    - For CustomOpDef: Uses the decorated function
    - For OpOverload: Traces the op call, which falls through to normal inductor lowering

    Examples:
        # Static configs
        @torch.library.custom_op("mylib::attention", mutates_args=())
        def my_attention(query, key, value, head_dim=32):
            ...

        register_custom_op_autotuning(
            my_attention,
            configs=[
                CustomOpConfig(attention_impl, head_dim=32, method='chunked'),
                CustomOpConfig(attention_impl, head_dim=64, method='tiled'),
                CustomOpConfig(head_dim=128),  # No decomposition specified, use default
            ],
            input_gen_fns={
                "query": lambda fake: torch.randn_like(fake, device='cuda'),
                "key": lambda fake: torch.randn_like(fake, device='cuda'),
                "value": lambda fake: torch.randn_like(fake, device='cuda'),
            },
        )

        # Dynamic config generation based on input tensor properties
        def generate_k_split_configs(fake_tensors: dict[str, torch.Tensor]) -> list[CustomOpConfig]:
            # Access tensor shapes, dtypes, devices, etc.
            m, k = fake_tensors["mat1"].shape
            _, n = fake_tensors["mat2"].shape
            k_splits = ... # compute possible k splits based on tensor properties
            return [CustomOpConfig(k_splits=k) for k in k_splits]

        register_custom_op_autotuning(
            matmul_decomposeK_op,
            config_generator=generate_k_split_configs,
            input_gen_fns={...},
        )

    Range-based Example:
        register_custom_op_autotuning(
            my_op,
            configs=[CustomOpConfig(impl1), CustomOpConfig(impl2), CustomOpConfig(impl3)],
            dispatch_on={
                # Dispatch based on x.shape[1]
                "tensor_name": "x",
                "dim": 1,
                # Optional Benchmark size used for the unbounded range [2049, inf].
                # Since inf is not a concrete value, we use range_upper_bound as the benchmark size.
                # Default value is 65536 (DEFAULT_RANGE_UPPER_BOUND) if not provided.
                "range_upper_bound": 8192,
            },
            split_points=[512, 2048],  # Creates ranges: [1,512], [513,2048], [2049, 8192]
        )
    """
    from torch._library.custom_ops import CustomOpDef

    # Handle both CustomOpDef and OpOverload - derive impl_fn automatically
    # Both cases call through op_overload so fake handlers are used during tracing
    if isinstance(custom_op, CustomOpDef):
        op_overload = custom_op._opoverload
    elif isinstance(custom_op, torch._ops.OpOverload):
        op_overload = custom_op
    else:
        raise TypeError(
            f"custom_op must be a CustomOpDef or OpOverload, got {type(custom_op)}."
        )

    # impl_fn calls through op_overload so fake handlers are used during tracing
    def impl_fn(*args, **kwargs):
        return op_overload(*args, **kwargs)

    # Validate configs and config_generator are mutually exclusive
    if configs is not None and config_generator is not None:
        raise ValueError(
            "Cannot specify both 'configs' and 'config_generator'. "
            "Use 'config_generator' for shape-dependent configs."
        )

    if configs is None and config_generator is None:
        raise ValueError("Must specify either 'configs' or 'config_generator'")

    # Process and validate static configs at registration time
    static_configs = None
    if configs is not None:
        if not isinstance(configs, (list, tuple)):
            raise TypeError(f"configs must be a list or tuple, got {type(configs)}")

        static_configs = []
        for cfg in configs:
            if isinstance(cfg, CustomOpConfig):
                static_configs.append(cfg)
            else:
                raise TypeError(
                    f"Each config must be a CustomOpConfig object, got {type(cfg)}"
                )

        if not static_configs:
            raise ValueError("At least one config must be provided")

    if name is None:
        name = f"{op_overload._name}_autotuned"

    # Validate range-based parameters
    is_range_based = dispatch_on is not None or split_points is not None
    dispatch_on_tuple: tuple[str, int] | None = None
    range_upper_bound = DEFAULT_RANGE_UPPER_BOUND
    if is_range_based:
        if dispatch_on is None or split_points is None:
            raise ValueError(
                "Both dispatch_on and split_points must be specified for range-based autotuning"
            )
        if not isinstance(dispatch_on, dict):
            raise ValueError(
                "dispatch_on must be a dict with 'tensor_name' and 'dim' keys, "
                f"e.g., {{'tensor_name': 'x', 'dim': 1}}. Got: {type(dispatch_on)}"
            )
        if "tensor_name" not in dispatch_on or "dim" not in dispatch_on:
            raise ValueError(
                "dispatch_on must contain 'tensor_name' and 'dim' keys, "
                f"e.g., {{'tensor_name': 'x', 'dim': 1}}. Got keys: {list(dispatch_on.keys())}"
            )
        if not isinstance(dispatch_on["tensor_name"], str):
            raise ValueError(
                f"dispatch_on['tensor_name'] must be a string (tensor parameter name), "
                f"got {type(dispatch_on['tensor_name'])}"
            )
        if not isinstance(dispatch_on["dim"], int):
            raise ValueError(
                f"dispatch_on['dim'] must be an integer (dimension index), "
                f"got {type(dispatch_on['dim'])}"
            )
        dispatch_on_tuple = (dispatch_on["tensor_name"], dispatch_on["dim"])
        range_upper_bound = dispatch_on.get(
            "range_upper_bound", DEFAULT_RANGE_UPPER_BOUND
        )
        if not isinstance(range_upper_bound, int) or range_upper_bound <= 0:
            raise ValueError(
                f"dispatch_on['range_upper_bound'] must be a positive integer, "
                f"got {range_upper_bound}"
            )
        if not isinstance(split_points, list) or len(split_points) == 0:
            raise ValueError("split_points must be a non-empty list of integers")
        if sorted(split_points) != split_points:
            raise ValueError("split_points must be sorted in ascending order")

    # Create and register the lowering function
    lowering_fn = _create_autotuning_lowering(
        # pyrefly: ignore [bad-argument-type]
        processed_configs=static_configs,
        default_impl=impl_fn,
        name=name,
        op_overload=op_overload,
        input_gen_fns=input_gen_fns,
        is_range_based=is_range_based,
        config_generator=config_generator,
        dispatch_on=dispatch_on_tuple,
        split_points=split_points,
        range_upper_bound=range_upper_bound,
        min_speedup_threshold=min_speedup_threshold,
        benchmark_with_cudagraphs=benchmark_with_cudagraphs,
    )

    # Register in user_lowerings which takes priority over built-in lowerings
    # The dispatch in graph.py checks user_lowerings first with recursion guard
    user_lowerings[op_overload] = lowering_fn