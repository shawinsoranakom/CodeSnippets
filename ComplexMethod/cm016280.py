def gen_pyi(
    native_yaml_path: str,
    tags_yaml_path: str,
    deprecated_yaml_path: str,
    fm: FileManager,
) -> None:
    """gen_pyi()

    This function generates a pyi file for torch.
    """

    # Some of this logic overlaps with generate_python_signature in
    # tools/autograd/gen_python_functions.py; however, this
    # function is all about generating mypy type signatures, whereas
    # the other function generates are custom format for argument
    # checking.  If you are update this, consider if your change
    # also needs to update the other file.

    # Dictionary for NamedTuple definitions
    structseqs: dict[str, str] = {}

    # Generate type signatures for top-level functions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    unsorted_function_hints: dict[str, list[str]] = collections.defaultdict(list)

    for n, n1, n2 in [
        ("csr", "crow", "col"),
        ("csc", "ccol", "row"),
        ("bsr", "crow", "col"),
        ("bsc", "ccol", "row"),
    ]:
        unsorted_function_hints.update(
            {
                f"sparse_{n}_tensor": [
                    defs(
                        f"sparse_{n}_tensor",
                        [
                            f"{n1}_indices: Tensor | list",
                            f"{n2}_indices: Tensor | list",
                            "values: Tensor | list",
                            "size: _size | None = None",
                            "*",
                            "dtype: _dtype | None = None",
                            "device: DeviceLikeType | None = None",
                            "requires_grad: _bool = False",
                            "check_invariants: _bool | None = None",
                        ],
                        "Tensor",
                    )
                ],
            }
        )

    unsorted_function_hints.update(
        {
            "set_flush_denormal": [
                defs("set_flush_denormal", ["mode: _bool"], "_bool")
            ],
            "get_default_dtype": [defs("get_default_dtype", [], "_dtype")],
            "asarray": [
                defs(
                    "asarray",
                    [
                        "obj: Any",
                        "*",
                        "dtype: _dtype | None = None",
                        "device: DeviceLikeType | None = None",
                        "copy: _bool | None = None",
                        "requires_grad: _bool | None = None",
                    ],
                    "Tensor",
                )
            ],
            "from_numpy": [defs("from_numpy", ["ndarray"], "Tensor")],
            "frombuffer": [
                defs(
                    "frombuffer",
                    [
                        "buffer: Any",
                        "*",
                        "dtype: _dtype",
                        "count: int = -1",
                        "offset: int = 0",
                        "requires_grad: _bool = False",
                    ],
                    "Tensor",
                )
            ],
            "numel": [defs("numel", ["self: Tensor"], "_int")],
            "as_tensor": [
                defs(
                    "as_tensor",
                    ["data: Any", "dtype: _dtype | None = None", DEVICE_PARAM],
                    "Tensor",
                )
            ],
            "get_num_threads": [defs("get_num_threads", [], "_int")],
            "set_num_threads": [defs("set_num_threads", ["num: _int"], "None")],
            "init_num_threads": [defs("init_num_threads", [], "None")],
            "get_num_interop_threads": [defs("get_num_interop_threads", [], "_int")],
            "set_num_interop_threads": [
                defs("set_num_interop_threads", ["num: _int"], "None")
            ],
            # These functions are explicitly disabled by
            # SKIP_PYTHON_BINDINGS because they are hand bound.
            # Correspondingly, we must hand-write their signatures.
            "tensor": [defs("tensor", ["data: Any", *FACTORY_PARAMS], "Tensor")],
            "sparse_coo_tensor": [
                defs(
                    "sparse_coo_tensor",
                    [
                        "indices: Tensor",
                        "values: Tensor | list",
                        "size: _size | None = None",
                        "*",
                        "dtype: _dtype | None = None",
                        "device: DeviceLikeType | None = None",
                        "requires_grad: _bool = False",
                        "check_invariants: _bool | None = None",
                        "is_coalesced: _bool | None = None",
                    ],
                    "Tensor",
                )
            ],
            "sparse_compressed_tensor": [
                defs(
                    "sparse_compressed_tensor",
                    [
                        "compressed_indices: Tensor | list",
                        "plain_indices: Tensor | list",
                        "values: Tensor | list",
                        "size: _size | None = None",
                        "*",
                        "dtype: _dtype | None = None",
                        "layout: _layout | None = None",
                        "device: DeviceLikeType | None = None",
                        "requires_grad: _bool = False",
                        "check_invariants: _bool | None = None",
                    ],
                    "Tensor",
                )
            ],
            "_sync": [defs("_sync", ["t: Tensor"], "None")],
            "_is_functional_tensor": [
                defs("_is_functional_tensor", ["t: Tensor"], "_bool")
            ],
            "_is_functional_tensor_base": [
                "def _is_functional_tensor_base(t: Tensor) -> _bool: ..."
            ],
            "_from_functional_tensor": [
                defs("_from_functional_tensor", ["t: Tensor"], "Tensor")
            ],
            "_to_functional_tensor": [
                defs("_to_functional_tensor", ["t: Tensor"], "Tensor")
            ],
            "_functionalize_replace": [
                defs(
                    "_functionalize_replace", ["self_: Tensor", "other: Tensor"], "None"
                )
            ],
            "_functionalize_commit_update": [
                defs("_functionalize_commit_update", ["t: Tensor"], "None")
            ],
            "_functionalize_unsafe_set": [
                "def _functionalize_unsafe_set(dst: Tensor, src: Tensor) -> None: ..."
            ],
            "_functionalize_mark_mutation_hidden_from_autograd": [
                defs(
                    "_functionalize_mark_mutation_hidden_from_autograd",
                    ["t: Tensor"],
                    "None",
                )
            ],
            "_functionalize_mutation_counter": [
                defs(
                    "_functionalize_mutation_counter",
                    ["t: Tensor"],
                    "_int",
                )
            ],
            "_functionalize_storage_changed_counter": [
                defs(
                    "_functionalize_storage_changed_counter",
                    ["t: Tensor"],
                    "_int",
                )
            ],
            "_functionalize_inductor_storage_resized_counter": [
                defs(
                    "_functionalize_inductor_storage_resized_counter",
                    ["t: Tensor"],
                    "_int",
                )
            ],
            "_functionalize_are_all_mutations_hidden_from_autograd": [
                defs(
                    "_functionalize_are_all_mutations_hidden_from_autograd",
                    ["t: Tensor"],
                    "_bool",
                )
            ],
            "_functionalize_are_all_mutations_under_no_grad_or_inference_mode": [
                defs(
                    "_functionalize_are_all_mutations_under_no_grad_or_inference_mode",
                    ["t: Tensor"],
                    "_bool",
                )
            ],
            "_functionalize_was_inductor_storage_resized": [
                defs(
                    "_functionalize_was_inductor_storage_resized",
                    ["t: Tensor"],
                    "_bool",
                )
            ],
            "_functionalize_sync": [defs("_functionalize_sync", ["t: Tensor"], "None")],
            "_functionalize_was_storage_changed": [
                defs("_functionalize_was_storage_changed", ["tensor: Tensor"], "_bool")
            ],
            "_functionalize_mark_storage_changed": [
                "def _functionalize_mark_storage_changed(tensor: Tensor) -> _bool: ..."
            ],
            "_functionalize_has_metadata_mutation": [
                defs(
                    "_functionalize_has_metadata_mutation", ["tensor: Tensor"], "_bool"
                )
            ],
            "_functionalize_apply_view_metas": [
                defs(
                    "_functionalize_apply_view_metas",
                    ["tensor: Tensor", "base: Tensor"],
                    "Tensor",
                )
            ],
            "_functionalize_is_symbolic": [
                defs("_functionalize_is_symbolic", ["tensor: Tensor"], "_bool")
            ],
            "_enable_functionalization": [
                defs(
                    "_enable_functionalization",
                    ["*", "reapply_views: _bool = False"],
                    "None",
                )
            ],
            "_disable_functionalization": [defs("_disable_functionalization")],
            "range": [
                defs(
                    "range",
                    [
                        "start: Number",
                        "end: Number",
                        "step: Number = 1",
                        "*",
                        "out: Tensor | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                )
            ],
            "arange": [
                defs(
                    "arange",
                    [
                        "start: Number",
                        "end: Number",
                        "step: Number",
                        "*",
                        "out: Tensor | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
                defs(
                    "arange",
                    [
                        "start: Number",
                        "end: Number",
                        "*",
                        "out: Tensor | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
                defs(
                    "arange",
                    ["end: Number", "*", "out: Tensor | None = None", *FACTORY_PARAMS],
                    "Tensor",
                ),
            ],
            "linspace": [
                defs(
                    "linspace",
                    [
                        "start: Number",
                        "end: Number",
                        "steps: _int | None = None",
                        "*",
                        "out: Tensor | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                )
            ],
            "logspace": [
                defs(
                    "logspace",
                    [
                        "start: Number",
                        "end: Number",
                        "steps: _int | None = None",
                        "base: _float = 10.0",
                        "*",
                        "out: Tensor | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                )
            ],
            "randint": [
                defs(
                    "randint",
                    [
                        "low: _int",
                        "high: _int",
                        "size: _size",
                        "*",
                        "generator: Generator | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
                defs(
                    "randint",
                    [
                        "high: _int",
                        "size: _size",
                        "*",
                        "generator: Generator | None = None",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
            ],
            "full": [
                defs(
                    "full",
                    [
                        "size: _size",
                        "fill_value: Number | _complex",
                        "*",
                        "out: Tensor | None = None",
                        "layout: _layout = strided",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
                defs(
                    "full",
                    [
                        "size: _size",
                        "fill_value: Number | _complex",
                        "*",
                        "names: list[str | None]",
                        "layout: _layout = strided",
                        *FACTORY_PARAMS,
                    ],
                    "Tensor",
                ),
            ],
            "is_grad_enabled": [defs("is_grad_enabled", [], "_bool")],
            "is_inference_mode_enabled": [
                defs("is_inference_mode_enabled", [], "_bool")
            ],
            "nonzero": [
                defs(
                    "nonzero",
                    [
                        "input: Tensor",
                        "*",
                        "as_tuple: Literal[False] = False",
                        "out: Tensor | None = None",
                    ],
                    "Tensor",
                ),
                defs(
                    "nonzero",
                    ["input: Tensor", "*", "as_tuple: Literal[True]"],
                    "tuple[Tensor, ...]",
                ),
            ],
            "dsmm": [defs("dsmm", ["input: Tensor", "mat2: Tensor"], "Tensor")],
            "hsmm": [defs("hsmm", ["input: Tensor", "mat2: Tensor"], "Tensor")],
            "saddmm": [
                defs(
                    "saddmm",
                    [
                        "input: Tensor",
                        "mat1: Tensor",
                        "mat2: Tensor",
                        "*",
                        "beta: Number = 1",
                        "alpha: Number = 1",
                        "out: Tensor | None = None",
                    ],
                    "Tensor",
                )
            ],
            "spmm": [defs("spmm", ["input: Tensor", "mat2: Tensor"], "Tensor")],
            "div": [
                defs(
                    "div",
                    [
                        "input: Tensor | Number",
                        "other: Tensor | Number",
                        "*",
                        "rounding_mode: str | None = None",
                        "out: Tensor | None = None",
                    ],
                    "Tensor",
                )
            ],
        }
    )
    for binop in ["true_divide", "floor_divide"]:
        unsorted_function_hints[binop].append(
            defs(
                binop,
                [
                    "input: Tensor | Number",
                    "other: Tensor | Number",
                    "*",
                    "out: Tensor | None = None",
                ],
                "Tensor",
            )
        )
    for binop in ["mul"]:
        unsorted_function_hints[binop].append(
            defs(
                binop,
                [
                    "input: Tensor | Number | _complex",
                    "other: Tensor | Number | _complex",
                    "*",
                    "out: Tensor | None = None",
                ],
                "Tensor",
            )
        )
    for binop in ["add", "sub"]:
        unsorted_function_hints[binop].append(
            defs(
                binop,
                [
                    "input: Tensor | Number | _complex",
                    "other: Tensor | Number | _complex",
                    "*",
                    "alpha: Number | _complex | None = 1",
                    "out: Tensor | None = None",
                ],
                "Tensor",
            )
        )

    native_functions = parse_native_yaml(
        native_yaml_path, tags_yaml_path
    ).native_functions
    native_functions = list(filter(should_generate_py_binding, native_functions))

    function_signatures = load_signatures(
        native_functions, deprecated_yaml_path, method=False, pyi=True
    )
    sig_groups = get_py_torch_functions(function_signatures)
    for group in sorted(sig_groups, key=lambda g: g.signature.name):
        name = group.signature.name
        unsorted_function_hints[name] += generate_type_hints(group)

        structseq = returns_structseq_pyi(group.signature)
        if structseq is not None and not group.signature.deprecated:
            # deprecated structseqs are currently not included for torch functions
            tuple_name, tuple_def = structseq
            if tuple_name in structseqs:
                if structseqs[tuple_name] != tuple_def:
                    raise AssertionError(
                        f"Duplicate structseq {tuple_name} with different definition"
                    )
            else:
                structseqs[tuple_name] = tuple_def

    def replace_special_case(hint: str) -> str:
        # NB: Keep this in sync with enum in aten/src/ATen/core/Reduction.h
        hint = hint.replace("at::Reduction::Mean", "1")
        hint = hint.replace(": Tensor = None", ": Tensor | None = None")
        return hint

    docstrs = gather_docstrs()
    function_hints = []
    for name, hints in sorted(unsorted_function_hints.items()):
        hints = [replace_special_case(h) for h in hints]
        if len(hints) > 1:
            hints = ["@overload\n" + h for h in hints]
        docstr = docstrs.get(f"torch.{name}")
        if docstr is not None:
            hints = [add_docstr_to_hint(docstr, h) for h in hints]
        function_hints += hints

    # Generate type signatures for Tensor methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    index_type_def = [_index_type_def]
    unsorted_tensor_method_hints: dict[str, list[str]] = collections.defaultdict(list)
    unsorted_tensor_method_hints.update(
        {
            "size": [
                defs("size", ["self", "dim: None = None"], "Size"),
                defs("size", ["self", "dim: _int"], "_int"),
            ],
            "stride": [
                defs("stride", ["self", "dim: None = None"], "tuple[_int, ...]"),
                defs("stride", ["self", "dim: _int"], "_int"),
            ],
            "new_ones": [
                defs("new_ones", ["self", "size: _size", *FACTORY_PARAMS], "Tensor")
            ],
            "new_tensor": [
                defs("new_tensor", ["self", "data: Any", *FACTORY_PARAMS], "Tensor")
            ],
            "__new__": [defs("__new__", ["cls", "*args", "**kwargs"], "Self")],
            # new and __init__ have the same signatures differ only in return type
            # Adapted from legacy_tensor_ctor and legacy_tensor_new
            "new": [
                defs("new", ["cls", "*args: Any", DEVICE_PARAM], "Self"),
                defs("new", ["cls", "storage: Storage"], "Self"),
                defs("new", ["cls", "other: Tensor"], "Self"),
                defs("new", ["cls", "size: _size", "*", DEVICE_PARAM], "Self"),
            ],
            "__init__": [
                defs("__init__", ["self", "*args: Any", DEVICE_PARAM], "None"),
                defs("__init__", ["self", "storage: Storage"], "None"),
                defs("__init__", ["self", "other: Tensor"], "None"),
                defs("__init__", ["self", "size: _size", "*", DEVICE_PARAM], "None"),
            ],
            "as_subclass": [defs("as_subclass", ["self", "cls: type[S]"], "S")],
            "_make_subclass": [
                "@staticmethod\n"
                + defs(
                    "_make_subclass",
                    [
                        "cls: type[S]",
                        "data: Tensor",
                        "require_grad: _bool = False",
                        "dispatch_strides: _bool = False",
                        "dispatch_device: _bool = False",
                        "device_for_backend_keys: _device | None = None",
                    ],
                    "S",
                )
            ],
            "_make_wrapper_subclass": [
                "@staticmethod\n"
                + defs(
                    "_make_wrapper_subclass",
                    [
                        "cls: type[S]",
                        "size: Sequence[_int | SymInt]",
                        "strides: Sequence[_int | SymInt] | None = None",
                        "storage_offset: _int | SymInt | None = None",
                        "memory_format: torch.memory_format | None = None",
                        "dtype: _dtype | None = None",
                        "layout: _layout = strided",
                        "device: _device | None = None",
                        "pin_memory: _bool = False",
                        "requires_grad: _bool = False",
                        "dispatch_sizes_strides_policy: str | None = None",
                        "dispatch_device: _bool = False",
                        "dispatch_layout: _bool = False",
                        "_extra_dispatch_keys: torch.DispatchKeySet | None = None",
                        "storage_size: _int | SymInt | None = None",
                    ],
                    "S",
                )
            ],
            "_dtensor__new__": [
                "@staticmethod\n"
                + defs(
                    "_dtensor__new__",
                    [
                        "cls: type[S]",
                        "local_tensor: Tensor",
                        "spec: torch.distributed.tensor._dtensor_spec.DTensorSpec",
                        "requires_grad: _bool",
                    ],
                    "S",
                )
            ],
            "__contains__": [defs("__contains__", ["self", "item: Any", "/"], "_bool")],
            "__getitem__": [defs("__getitem__", ["self", INDICES, "/"], "Tensor")],
            "__setitem__": [
                defs(
                    "__setitem__",
                    ["self", INDICES, "value: Tensor | Number", "/"],
                    "None",
                )
            ],
            "tolist": [defs("tolist", ["self"], "list")],
            "requires_grad_": [
                defs("requires_grad_", ["self", "mode: _bool = True"], "Tensor")
            ],
            "element_size": [defs("element_size", ["self"], "_int")],
            "data_ptr": [defs("data_ptr", ["self"], "_int")],
            "dim": [defs("dim", ["self"], "_int")],
            "nonzero": [
                defs(
                    "nonzero",
                    ["self", "*", "as_tuple: Literal[False] = False"],
                    "Tensor",
                ),
                defs(
                    "nonzero",
                    ["self", "*", "as_tuple: Literal[True]"],
                    "tuple[Tensor, ...]",
                ),
            ],
            "numel": [defs("numel", ["self"], "_int")],
            "ndimension": [defs("ndimension", ["self"], "_int")],
            "nelement": [defs("nelement", ["self"], "_int")],
            "cuda": [
                defs(
                    "cuda",
                    [
                        "self",
                        "device: _device | _int | str | None = None",
                        "non_blocking: _bool = False",
                        "memory_format: torch.memory_format = torch.preserve_format",
                    ],
                    "Tensor",
                )
            ],
            "xpu": [
                defs(
                    "xpu",
                    [
                        "self",
                        "device: _device | _int | str | None = None",
                        "non_blocking: _bool = False",
                        "memory_format: torch.memory_format = torch.preserve_format",
                    ],
                    "Tensor",
                )
            ],
            "cpu": [
                defs(
                    "cpu",
                    [
                        "self",
                        "memory_format: torch.memory_format = torch.preserve_format",
                    ],
                    "Tensor",
                )
            ],
            "numpy": [
                defs("numpy", ["self", "*", "force: _bool = False"], "numpy.ndarray")
            ],
            "apply_": [defs("apply_", ["self", "callable: Callable"], "Tensor")],
            "map_": [
                defs("map_", ["self", "other: Tensor", "callable: Callable"], "Tensor")
            ],
            "map2_": [
                defs(
                    "map2_",
                    ["self", "x: Tensor", "y: Tensor", "callable: Callable"],
                    "Tensor",
                )
            ],
            "storage": [defs("untyped_storage", ["self"], "UntypedStorage")],
            "storage_type": [defs("storage_type", ["self"], "Storage")],
            "type": [
                defs(
                    "type",
                    ["self", "dtype: None = None", "non_blocking: _bool = False"],
                    "str",
                ),
                defs(
                    "type",
                    ["self", "dtype: str | _dtype", "non_blocking: _bool = False"],
                    "Tensor",
                ),
            ],
            "get_device": [defs("get_device", ["self"], "_int")],
            "contiguous": [
                defs(
                    "contiguous",
                    [
                        "self",
                        "memory_format: torch.memory_format = torch.contiguous_format",
                    ],
                    "Tensor",
                )
            ],
            "has_names": [defs("has_names", ["self"], "_bool")],
            "is_contiguous": [
                defs(
                    "is_contiguous",
                    [
                        "self",
                        "memory_format: torch.memory_format = torch.contiguous_format",
                    ],
                    "_bool",
                )
            ],
            "_is_view": [defs("_is_view", ["self"], "_bool")],
            "is_cpu": ["is_cpu: _bool"],
            "is_cuda": ["is_cuda: _bool"],
            "is_xpu": ["is_xpu: _bool"],
            "is_leaf": ["is_leaf: _bool"],
            "is_nested": ["is_nested: _bool"],
            "is_sparse": ["is_sparse: _bool"],
            "is_sparse_csr": ["is_sparse_csr: _bool"],
            "is_quantized": ["is_quantized: _bool"],
            "is_meta": ["is_meta: _bool"],
            "is_mps": ["is_mps: _bool"],
            "is_mtia": ["is_mtia: _bool"],
            "is_maia": ["is_maia: _bool"],
            "is_mkldnn": ["is_mkldnn: _bool"],
            "is_vulkan": ["is_vulkan: _bool"],
            "is_ipu": ["is_ipu: _bool"],
            "storage_offset": [defs("storage_offset", ["self"], "_int | SymInt")],
            "to": [
                (
                    defs(
                        "to",
                        [
                            "self",
                            *to_args,
                            "non_blocking: _bool = False",
                            "copy: _bool = False",
                            "*",
                            "memory_format: torch.memory_format | None = None",
                        ],
                        "Tensor",
                    )
                )
                for to_args in [
                    ["dtype: _dtype"],
                    [
                        "device: DeviceLikeType | None = None",
                        "dtype: _dtype | None = None",
                    ],
                    ["other: Tensor"],
                ]
            ],
            "item": [defs("item", ["self"], "Number")],
            "copy_": [
                defs(
                    "copy_",
                    ["self", "other: Tensor", "non_blocking: _bool = False"],
                    "Tensor",
                )
            ],
            "set_": [
                defs(
                    "set_",
                    [
                        "self",
                        "source: Storage | TypedStorage | UntypedStorage",
                        "storage_offset: IntLikeType",
                        "size: _symsize",
                        "stride: _symsize",
                    ],
                    "Tensor",
                ),
                defs(
                    "set_",
                    ["self", "source: Storage | TypedStorage | UntypedStorage"],
                    "Tensor",
                ),
            ],
            "split": [
                defs(
                    "split",
                    ["self", "split_size: _int", "dim: _int = 0"],
                    "Sequence[Tensor]",
                ),
                defs(
                    "split",
                    ["self", "split_size: tuple[_int, ...]", "dim: _int = 0"],
                    "Sequence[Tensor]",
                ),
            ],
            "div": [
                defs(
                    "div",
                    [
                        "self",
                        "other: Tensor | Number",
                        "*",
                        "rounding_mode: str | None = None",
                    ],
                    "Tensor",
                )
            ],
            "div_": [
                defs(
                    "div_",
                    [
                        "self",
                        "other: Tensor | Number",
                        "*",
                        "rounding_mode: str | None = None",
                    ],
                    "Tensor",
                )
            ],
        }
    )
    for binop in ["true_divide", "floor_divide"]:
        for inplace in [False, True]:
            out_args = ["*", "out: Tensor | None = None"]
            if inplace:
                binop += "_"
                out_args = []
            unsorted_tensor_method_hints[binop].append(
                defs(
                    binop,
                    [
                        "self",
                        "other: Tensor | Number | torch.SymInt | torch.SymFloat",
                        *out_args,
                    ],
                    "Tensor",
                )
            )
    for binop in ["mul"]:
        for inplace in [False, True]:
            out_args = ["*", "out: Tensor | None = None"]
            if inplace:
                binop += "_"
                out_args = []
            unsorted_tensor_method_hints[binop].append(
                defs(
                    binop,
                    [
                        "self",
                        "other: Tensor | Number | _complex | torch.SymInt | torch.SymFloat",
                        *out_args,
                    ],
                    "Tensor",
                )
            )
    for binop in ["add", "sub"]:
        for inplace in [False, True]:
            out_args = ["out: Tensor | None = None"]
            if inplace:
                binop += "_"
                out_args = []
            unsorted_tensor_method_hints[binop].append(
                defs(
                    binop,
                    [
                        "self",
                        "other: Tensor | Number | _complex | torch.SymInt | torch.SymFloat",
                        "*",
                        "alpha: Number | _complex | None = 1",
                        *out_args,
                    ],
                    "Tensor",
                )
            )
    simple_conversions = [
        "bfloat16",
        "bool",
        "byte",
        "char",
        "double",
        "float",
        "half",
        "int",
        "long",
        "short",
    ]
    for name in simple_conversions:
        unsorted_tensor_method_hints[name].append(f"def {name}(self) -> Tensor: ...")

    # pyi tensor methods don't currently include deprecated signatures for some reason
    # TODO: we should probably add them in
    tensor_method_signatures = load_signatures(
        native_functions,
        deprecated_yaml_path,
        method=True,
        skip_deprecated=True,
        pyi=True,
    )
    tensor_method_sig_groups = get_py_torch_functions(
        tensor_method_signatures, method=True
    )

    for group in sorted(tensor_method_sig_groups, key=lambda g: g.signature.name):
        name = group.signature.name
        unsorted_tensor_method_hints[name] += generate_type_hints(group)

        structseq = returns_structseq_pyi(group.signature)
        if structseq is not None and not group.signature.deprecated:
            # deprecated structseqs are currently not included for torch functions
            tuple_name, tuple_def = structseq
            if tuple_name in structseqs:
                if structseqs[tuple_name] != tuple_def:
                    raise AssertionError(
                        f"Duplicate structseq {tuple_name} with different definition"
                    )
            else:
                structseqs[tuple_name] = tuple_def

    for op in all_ops:
        name = f"__{op}__"
        unsorted_tensor_method_hints[name] += sig_for_ops(name)

    tensor_method_hints = []
    for name, hints in sorted(unsorted_tensor_method_hints.items()):
        if len(hints) > 1:
            hints = ["@overload\n" + h for h in hints]
        docstr = docstrs.get(f"torch._C.TensorBase.{name}")
        if docstr is not None:
            hints = [add_docstr_to_hint(docstr, h) for h in hints]
        tensor_method_hints += hints

    # TODO: Missing type hints for nn

    # Generate structseq definitions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    structseqs = dict(sorted(structseqs.items()))
    structseq_defs = [f"{defn}\n" for defn in structseqs.values()]
    return_types___all__ = [
        "__all__ = [",
        '    "pytree_register_structseq",',
        '    "all_return_types",',
        *(f'    "{name}",' for name in structseqs),
        "]",
    ]

    # Generate type signatures for legacy classes
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    legacy_storage_base_hints = ["class StorageBase: ..."]

    legacy_class_hints = []
    for c in (
        "DoubleTensor",
        "FloatTensor",
        "BFloat16Tensor",
        "LongTensor",
        "IntTensor",
        "ShortTensor",
        "HalfTensor",
        "CharTensor",
        "ByteTensor",
        "BoolTensor",
    ):
        legacy_class_hints.append(f"class {c}(Tensor): ...")

    # Generate type signatures for dtype classes
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # TODO(#146647): don't explicitly list dtypes here; get it from canonical
    # source
    dtype_class_hints = [
        f"{n}: dtype = ..."
        for n in [
            "float32",
            "float",
            "float64",
            "double",
            "float16",
            "bfloat16",
            "float8_e4m3fn",
            "float8_e4m3fnuz",
            "float8_e5m2",
            "float8_e5m2fnuz",
            "float8_e8m0fnu",
            "float4_e2m1fn_x2",
            "half",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "short",
            "int32",
            "int",
            "int64",
            "long",
            "complex32",
            "complex64",
            "chalf",
            "cfloat",
            "complex128",
            "cdouble",
            "quint8",
            "qint8",
            "qint32",
            "bool",
            "quint4x2",
            "quint2x4",
            "bits1x8",
            "bits2x4",
            "bits4x2",
            "bits8",
            "bits16",
        ]
    ]

    # Generate __all__ directive
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Include only the functions that contain hints, to prevent undefined
    # symbols to be included in the `__all__` directive.
    hinted_function_names = {
        name for name, hint in unsorted_function_hints.items() if hint
    }
    all_symbols = sorted(hinted_function_names.union(structseqs))
    all_directive = [
        "__all__ = [",
        *(f'    "{name}",' for name in all_symbols),
        "]",
    ]

    # Dispatch key hints
    # ~~~~~~~~~~~~~~~~~~
    dispatch_key_hints = [f"{d.name} = ..." for d in DispatchKey]
    torch_dispatch_mode_key_hints = [f"{k.name} = ..." for k in _TorchDispatchModeKey]

    # Tags Enum type hints
    # ~~~~~~~~~~~~~~~~~~~~

    tag_names = sorted(parse_tags_yaml(tags_yaml_path))
    tag_attributes = "\n".join(
        f"{name} = {index}" for index, name in enumerate(tag_names)
    )

    # Write out the stub
    # ~~~~~~~~~~~~~~~~~~

    env = {
        "structseq_defs": structseq_defs,
        "return_types___all__": return_types___all__,
        "function_hints": function_hints,
        "index_type_def": index_type_def,
        "tensor_method_hints": tensor_method_hints,
        "legacy_class_hints": legacy_class_hints,
        "legacy_storage_base_hints": legacy_storage_base_hints,
        "dtype_class_hints": dtype_class_hints,
        "dispatch_key_hints": dispatch_key_hints,
        "torch_dispatch_mode_key_hints": torch_dispatch_mode_key_hints,
        "all_directive": all_directive,
        "tag_attributes": tag_attributes,
    }
    fm.write_with_template(
        "torch/_C/__init__.pyi",
        "torch/_C/__init__.pyi.in",
        lambda: env,
    )
    fm.write_with_template(
        "torch/_C/_VariableFunctions.pyi",
        "torch/_C/_VariableFunctions.pyi.in",
        lambda: env,
    )
    fm.write_with_template(
        "torch/_VF.pyi",
        "torch/_C/_VariableFunctions.pyi.in",
        lambda: env,
    )
    fm.write_with_template(
        "torch/return_types.pyi",
        "torch/_C/return_types.pyi.in",
        lambda: env,
    )
    gen_nn_functional(fm)