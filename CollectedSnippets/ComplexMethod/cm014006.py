def aot_graph_input_parser(
    func: Callable[[list[Tensor]], list[Tensor]],
    device: str = "cuda",
    sym_shapes: dict[str, int] | None = None,
    default_sym_shape: int | None = None,
) -> dict[str, Any]:
    """
    Takes in a function which has been printed with print_readable() and constructs kwargs to run it.

    Handles Tensor inputs, Symints, and a graph module which might have tensor constants.

    Consider a function `forward` defined as follows:

    def forward(self, primals_1: "f32[1001, 6]", primals_2: "f32[s0]", primals_3: "Sym(s0)",):
        _tensor_constant0: "i64[4190]" = self._tensor_constant0
        # Further implementation

    kwargs = aot_graph_input_parser(forward)
    forward(**kwargs)
    """

    from torch.utils._dtype_abbrs import dtype_abbrs

    dtype_map: dict[str, torch.dtype] = {
        value: key for key, value in dtype_abbrs.items()
    }
    dtype_pattern: str = "|".join(dtype_abbrs.values())

    # Extracting the source code from the function
    source = inspect.getsource(func)

    # Regular expressions
    tensor_assignment_regex = rf"(_tensor_constant\d+): \"({dtype_pattern})\[\s*(.*?)\s*\]\" = self\.(_tensor_constant\d+)"
    tensor_regex = rf"({dtype_pattern})\[\s*(.*?)\s*\]"
    sym_shape_regex = r"Sym\((s\d+)\)"

    class TensorContainer:
        "Container for tensors as attributes"

    # Dictionary for tensors from annotations
    kwargs: dict[str, Any] = {}

    sym_shapes_dict: dict[str, int] = sym_shapes or {}

    def get_sym_int(symint: str) -> int:
        torch._check(
            symint in sym_shapes_dict or default_sym_shape is not None,
            lambda: f"{symint} not in symbolic_shapes and default sym shape not passed in",
        )
        return sym_shapes_dict.get(symint, default_sym_shape)  # type: ignore[return-value]

    def gen_tensor(shape: torch._prims_common.ShapeType, dtype: torch.dtype) -> Tensor:
        # Resolve symbolic shapes to concrete values
        resolved_shape = []
        dynamic_dims = []
        for i, dim in enumerate(shape):
            dim = dim.strip()  # type: ignore[attr-defined]
            if "s" in dim:
                s = get_sym_int(dim)
                resolved_shape.append(s)
                dynamic_dims.append(i)
            else:
                if dim:
                    resolved_shape.append(int(dim))

        constructor = torch.randn if dtype.is_floating_point else torch.zeros
        out = constructor(resolved_shape, dtype=dtype, device=device)  # type: ignore[call-arg]
        for d in dynamic_dims:
            torch._dynamo.mark_dynamic(out, d)
        return out

    # Parse function annotations for tensor generation
    annotations = func.__annotations__
    for param, annotation in annotations.items():
        # Skip 'return' annotation
        if param == "return":
            continue

        match = re.search(tensor_regex, annotation)
        if match:
            data_type, shape_str = match.groups()
            shape = tuple(shape_str.split(","))
            dtype = dtype_map[data_type]
            # pyrefly: ignore [bad-argument-type]
            kwargs[param] = gen_tensor(shape, dtype)

        match = re.search(sym_shape_regex, annotation)
        if match:
            kwargs[param] = get_sym_int(match.group(1))

    if "self" in inspect.signature(func).parameters:
        container = TensorContainer()
        kwargs["self"] = container
        for match in re.finditer(tensor_assignment_regex, source):
            attr_name, data_type, shape_str, _ = match.groups()
            shape = tuple(shape_str.split(","))
            dtype = dtype_map[data_type]
            # pyrefly: ignore [bad-argument-type]
            setattr(container, attr_name, gen_tensor(shape, dtype))

    return kwargs