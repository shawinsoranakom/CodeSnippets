def _gen_python_code(
        self,
        nodes: _node_list,
        root_module: str,
        namespace: _Namespace,
        *,
        verbose: bool = False,
        include_stride: bool = False,
        include_device: bool = False,
        colored: bool = False,
        # Render each argument on its own line
        expanded_def: bool = False,
        record_func: bool = False,
        additional_meta: list[str] | None = None,
    ) -> PythonCode:
        free_vars: list[str] = []
        body: list[str] = []
        globals_: dict[str, Any] = {}
        wrapped_fns: dict[str, None] = {}

        # Wrap string in list to pass by reference
        maybe_return_annotation: list[str] = [""]
        include_stride = include_stride or (
            os.environ.get("FX_GRAPH_SHOW_STRIDE", "0") == "1"
        )
        include_device = include_device or (
            os.environ.get("FX_GRAPH_SHOW_DEVICE", "0") == "1"
        )
        include_meta = os.environ.get("FX_GRAPH_SHOW_META", "0") == "1"

        def add_global(name_hint: str, obj: Any) -> str:
            """Add an obj to be tracked as a global.

            We call this for names that reference objects external to the
            Graph, like functions or types.

            Returns: the global name that should be used to reference 'obj' in generated source.
            """
            if (
                _is_from_torch(obj) and obj != torch.device
            ):  # to support registering torch.device
                # HACK: workaround for how torch custom ops are registered. We
                # can't import them like normal modules so they must retain their
                # fully qualified name.
                return _get_qualified_name(obj)

            # normalize the name hint to get a proper identifier
            global_name = namespace.create_name(name_hint, obj)

            if global_name in globals_:
                if globals_[global_name] != obj:
                    raise AssertionError(
                        f"Global name {global_name} already assigned to different object"
                    )
                return global_name
            globals_[global_name] = obj
            return global_name

        # Pre-fill the globals table with registered builtins.
        for name, (_, obj) in _custom_builtins.items():
            add_global(name, obj)

        def type_repr(o: object) -> str:
            if o == ():
                # Empty tuple is used for empty tuple type annotation Tuple[()]
                return "()"

            typename = _type_repr(o)
            if isinstance(o, types.UnionType) and "|" in typename:
                # str | int
                args = [type_repr(arg) for arg in o.__args__]
                return "|".join(args)

            if origin_type := getattr(o, "__origin__", None):
                # list[...], typing.List[...], TensorType[...]

                if isinstance(o, typing._GenericAlias):  # type: ignore[attr-defined]
                    # This is a generic pre-PEP585 type, e.g. typing.List[torch.Tensor]
                    origin_type = _origin_type_map.get(origin_type, origin_type)

                origin_typename = add_global(_type_repr(origin_type), origin_type)

                if hasattr(o, "__args__") and o.__args__:
                    args = [type_repr(arg) for arg in o.__args__]
                    return f"{origin_typename}[{','.join(args)}]"
                else:
                    return origin_typename

            # Common case: this is a regular module name like 'foo.bar.baz'
            return add_global(typename, o)

        if colored:
            red = _color_fns["red"]
            dim_green = _color_fns["dim_green"]
            dim = _color_fns["dim"]
            dim_blue = _color_fns["dim_blue"]
            blue = _color_fns["blue"]
        else:
            red = _identity
            dim_green = _identity
            dim = _identity
            dim_blue = _identity
            blue = _identity

        def _get_repr(arg: object) -> str:
            if isinstance(arg, Node):  # first because common
                return repr(arg)
            elif isinstance(arg, tuple) and hasattr(arg, "_fields"):
                # Handle NamedTuples (if it has `_fields`) via add_global.
                qualified_name = _get_qualified_name(type(arg))
                global_name = add_global(qualified_name, type(arg))
                return f"{global_name}{repr(tuple(arg))}"
            elif isinstance(
                arg, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)
            ):
                qualified_name = _get_qualified_name(arg)
                global_name = add_global(qualified_name, arg)
                return f"{global_name}"
            elif isinstance(arg, enum.Enum):
                cls = arg.__class__
                clsname = add_global(cls.__name__, cls)
                return f"{clsname}.{arg.name}"
            elif isinstance(arg, torch.Tensor):
                size = list(arg.size())
                dtype = str(arg.dtype).split(".")[-1]
                return f"torch.Tensor(size={size}, dtype={dtype})"
            elif isinstance(arg, tuple):
                if len(arg) == 1:
                    return f"({_get_repr(arg[0])},)"
                else:
                    return "(" + ", ".join(_get_repr(a) for a in arg) + ")"
            elif isinstance(arg, list):
                return "[" + ", ".join(_get_repr(a) for a in arg) + "]"
            elif isinstance(arg, slice):
                return f"slice({_get_repr(arg.start)}, {_get_repr(arg.stop)}, {_get_repr(arg.step)})"
            elif is_opaque_value_type(type(arg)):
                obj_repr, opaque_types = get_opaque_obj_repr(arg)
                for n, t in opaque_types.items():
                    add_global(n, t)
                return obj_repr
            else:
                return blue(repr(arg))

        def _format_args(
            args: tuple[Argument, ...], kwargs: dict[str, Argument]
        ) -> str:
            res = [_get_repr(a) for a in args]
            res.extend([f"{k} = {_get_repr(v)}" for k, v in kwargs.items()])
            return ", ".join(res)

        # Run through reverse nodes and record the first instance of a use
        # of a given node. This represents the *last* use of the node in the
        # execution order of the program, which we will use to free unused
        # values
        node_to_last_use: dict[Node, Node] = {}
        user_to_last_uses: dict[Node, list[Node]] = {}

        def register_last_uses(n: Node, user: Node) -> None:
            if n not in node_to_last_use:
                node_to_last_use[n] = user
                user_to_last_uses.setdefault(user, []).append(n)

        for node in reversed(nodes):
            for input_node in node._input_nodes:
                register_last_uses(input_node, node)

        def delete_unused_values(user: Node) -> None:
            """
            Delete values after their last use. This ensures that values that are
            not used in the remainder of the code are freed and the memory usage
            of the code is optimal.
            """
            if user.op == "placeholder":
                return
            if user.op == "output":
                body.append("\n")
                return
            nodes_to_delete = user_to_last_uses.get(user, [])

            if len(user.users.keys()) == 0:
                # This node is not used by any others. however it's also not
                # removed by DCE since side-effect. We want to free it's outputs
                # right after its execution done to save memory.
                nodes_to_delete.append(user)

            if len(nodes_to_delete):
                to_delete_str = " = ".join(
                    [repr(n) for n in nodes_to_delete] + ["None"]
                )
                body.append(f";  {dim(to_delete_str)}\n")
            else:
                body.append("\n")

        prev_summary_str = None

        def append_stacktrace_summary(node: Node) -> None:
            """
            Append a summary of the stacktrace to the generated code. This is
            useful for debugging.
            """
            nonlocal prev_summary_str

            if node.op not in {"placeholder", "output"}:
                additional_meta_str = ""
                if additional_meta:
                    parts: list[str] = []
                    for key in additional_meta:
                        if key in node.meta:
                            parts.append(f"{key}: {node.meta[key]}")
                    if parts:
                        additional_meta_str = f"# {', '.join(parts)} "

                annotation_str = ""
                annotation = node.meta.get("custom", {})
                annotation_trunc = {}
                if annotation:
                    for key, value in annotation.items():
                        value_str = str(value)
                        if len(value_str) > 40:
                            annotation_trunc[key] = value_str[:40] + "..."
                        else:
                            annotation_trunc[key] = value
                    annotation_str = f" Annotation: {annotation_trunc}"

                stack_trace_str = "No stacktrace found for following nodes"
                if stack_trace := node.stack_trace:
                    if parsed_stack_trace := _parse_stack_trace(stack_trace):
                        stack_trace_str = parsed_stack_trace.get_summary_str()

                maybe_recompute_info = ""
                if hasattr(node, "meta") and node.meta:
                    # recompute tags are generated by torch.compile and put in the joint graph.
                    # These tags are load bearing enough that we want them to show up by default
                    # in tlparse, when you run torch.compile.
                    recompute = node.meta.get("recompute", None)
                    ac_graph_id = node.meta.get("ac_graph_id", None)

                    if recompute is not None and ac_graph_id is not None:
                        maybe_recompute_info = (
                            f" ac_graph_id: {str(ac_graph_id)} - {str(recompute.name)}"
                        )
                    elif recompute is not None:
                        maybe_recompute_info = f" recompute: {str(recompute.name)}"
                    elif ac_graph_id is not None:
                        maybe_recompute_info = f" ac_graph_id: {str(ac_graph_id)}"

                summary_str = f"\n{dim(f'{additional_meta_str}#{annotation_str}{maybe_recompute_info} {stack_trace_str}')}\n"

                if summary_str != prev_summary_str:
                    prev_summary_str = summary_str
                    body.append(summary_str)

        def stringify_shape(shape: Iterable[object]) -> str:
            return f"[{', '.join([str(x) for x in shape])}]"

        def emit_node(node: Node) -> None:
            maybe_type_annotation = (
                "" if node.type is None else f" : {type_repr(node.type)}"
            )
            maybe_comment = ""

            if verbose:
                # override annotation with more detailed information
                try:
                    from torch.distributed.tensor._api import DTensor, DTensorSpec

                    dtensorspec_format_shard_order_str = (
                        DTensorSpec.format_shard_order_str
                    )
                except ModuleNotFoundError:
                    DTensor = None  # type: ignore[assignment,misc]
                    dtensorspec_format_shard_order_str = None
                from torch.fx.experimental.proxy_tensor import py_sym_types
                from torch.fx.passes.shape_prop import TensorMetadata

                meta_val = node.meta.get(
                    "val",
                    node.meta.get("tensor_meta", node.meta.get("example_value", None)),
                )

                def _tensor_annotation(t: torch.Tensor) -> str:
                    stride = stringify_shape(t.stride()) if include_stride else ""
                    device = f"{t.device}" if include_device else ""
                    return (
                        f"{red(dtype_abbrs[t.dtype])}"
                        f"{blue(stringify_shape(t.shape))}"
                        f"{dim_blue(stride)}"
                        f"{dim_green(device)}"
                    )

                # use string as annotation, to make it valid python code
                if isinstance(meta_val, torch.Tensor) and meta_val.layout not in (
                    torch.sparse_csc,
                    torch.sparse_csr,
                ):
                    # Fake tensors cause tests to wobble, so do not custom print them.
                    is_plain = type(meta_val) is torch.Tensor or isinstance(
                        meta_val, torch._subclasses.FakeTensor
                    )
                    core = _tensor_annotation(meta_val)
                    if is_plain:
                        maybe_type_annotation = f': "{core}"'
                    elif type(meta_val) is DTensor:
                        if dtensorspec_format_shard_order_str is None:
                            raise AssertionError(
                                "dtensorspec_format_shard_order_str is None for DTensor"
                            )
                        dtensor_meta = dtensorspec_format_shard_order_str(
                            meta_val._spec.placements,  # type: ignore[attr-defined]
                            meta_val._spec.shard_order,  # type: ignore[attr-defined]
                        )
                        cls = meta_val.__class__.__name__
                        maybe_type_annotation = (
                            f': "{cls}({core}, {dim_green(dtensor_meta)})"'
                        )
                    else:
                        cls = meta_val.__class__.__name__
                        maybe_type_annotation = f': "{cls}({core})"'

                elif isinstance(meta_val, py_sym_types):
                    val_str = CodeGen._sym_repr(meta_val)
                    maybe_type_annotation = f': "Sym({val_str})"'

                elif isinstance(meta_val, TensorMetadata):
                    maybe_type_annotation = f': "{dtype_abbrs[meta_val.dtype]}{stringify_shape(meta_val.shape)}"'

            desc = None
            if expanded_def:
                desc = node.meta.get("desc", None)
                if desc is not None and node.op == "placeholder":
                    maybe_comment += f"  # {desc}"
                # output is handled specially

            if include_meta and hasattr(node, "meta") and node.meta:
                body.append('"""\n')
                for k, v in node.meta.items():
                    # use str over repr since repr is susceptible to sympy
                    # errors such as "cannot determine truth value of Relational"
                    # Pretty print the high-level dict with str() for values
                    body.append(
                        f"{k}: {pprint.pformat(str(v), width=80, compact=True)}\n"
                    )
                body.append('"""\n')

            if node.op == "placeholder":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str, got {type(node.target)}"
                    )
                maybe_default_arg = (
                    "" if not node.args else f" = {_get_repr(node.args[0])}"
                )
                free_vars.append(
                    f"{node.target}{maybe_type_annotation}{maybe_default_arg}{maybe_comment}"
                )
                raw_name = node.target.replace("*", "")
                if raw_name != repr(node):
                    body.append(f"{repr(node)} = {raw_name}\n")
                return
            elif node.op == "call_method":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for call_method, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {_format_target(_get_repr(node.args[0]), node.target)}"
                    f"({_format_args(node.args[1:], node.kwargs)})"
                )
                return
            elif node.op == "call_function":
                if not callable(node.target):
                    raise AssertionError(
                        f"Expected node.target to be callable, got {type(node.target)}"
                    )
                # pretty print operators
                if (
                    getattr(node.target, "__module__", "") == "_operator"
                    and node.target.__name__ in magic_methods
                ):
                    if not isinstance(node.args, tuple):
                        raise AssertionError(
                            f"Expected node.args to be tuple, got {type(node.args)}"
                        )
                    body.append(
                        f"{repr(node)}{maybe_type_annotation} = "
                        f"{magic_methods[node.target.__name__].format(*(_get_repr(a) for a in node.args))}"
                    )
                    return

                # pretty print inplace operators; required for jit.script to work properly
                # not currently supported in normal FX graphs, but generated by torchdynamo
                if (
                    getattr(node.target, "__module__", "") == "_operator"
                    and node.target.__name__ in inplace_methods
                ):
                    body.append(
                        f"{inplace_methods[node.target.__name__].format(*(_get_repr(a) for a in node.args))};  "
                        f"{repr(node)}{maybe_type_annotation} = {_get_repr(node.args[0])}"
                    )
                    return

                qualified_name = _get_qualified_name(node.target)
                global_name = add_global(qualified_name, node.target)
                # special case for getattr: node.args could be 2-argument or 3-argument
                # 2-argument: attribute access; 3-argument: fall through to attrib function call with default value
                if (
                    global_name == "getattr"
                    and isinstance(node.args, tuple)
                    and isinstance(node.args[1], str)
                    and node.args[1].isidentifier()
                    and len(node.args) == 2
                ):
                    body.append(
                        f"{repr(node)}{maybe_type_annotation} = {_format_target(_get_repr(node.args[0]), node.args[1])}"
                    )
                    return
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {global_name}({_format_args(node.args, node.kwargs)})"
                )
                if node.meta.get("is_wrapped", False):
                    wrapped_fns.setdefault(global_name)
                return
            elif node.op == "call_module":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for call_module, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = "
                    f"{_format_target(root_module, node.target)}({_format_args(node.args, node.kwargs)})"
                )
                return
            elif node.op == "get_attr":
                if not isinstance(node.target, str):
                    raise AssertionError(
                        f"Expected node.target to be str for get_attr, got {type(node.target)}"
                    )
                body.append(
                    f"{repr(node)}{maybe_type_annotation} = {_format_target(root_module, node.target)}"
                )
                return
            elif node.op == "output":
                if node.type is not None:
                    maybe_return_annotation[0] = f" -> {type_repr(node.type)}"
                body.append(
                    self._call_method_with_signature_check(
                        self.generate_output,
                        node.args[0],
                        descs=desc if expanded_def else None,
                        repr_fn=_get_repr,
                    )
                )
                return
            raise NotImplementedError(f"node: {node.op} {node.target}")

        if record_func:
            body.append(
                "_rf = torch._C._profiler._RecordFunctionFast('## ENTER_GRAPH_PLACEHOLDER_KEY ##'); _rf.__enter__()\n"
            )
        for i, node in enumerate(nodes):
            # NOTE: emit_node does not emit a string with newline. It depends
            # on delete_unused_values to append one
            if verbose:
                append_stacktrace_summary(node)
            # emit a counter comment to keep track of
            # node index, which will be deleted later
            # after going through _body_transformer
            body.append(f"# COUNTER: {i}\n")
            do_record = record_func and node.op in (
                "call_function",
                "call_method",
                "call_module",
            )
            if do_record:
                # The double hash ## convention is used by post-processing to find the fx markers
                body.append(
                    f"_rf_{node.name} = torch._C._profiler._RecordFunctionFast('## {i} ##'); _rf_{node.name}.__enter__()\n"
                )
            emit_node(node)
            delete_unused_values(node)
            if do_record:
                body.append(f"_rf_{node.name}.__exit__(None, None, None)\n")
        if record_func:
            body.append("_rf.__exit__(None, None, None)\n")

        if len(body) == 0:
            # If the Graph has no non-placeholder nodes, no lines for the body
            # have been emitted. To continue to have valid Python code, emit a
            # single pass statement
            body.append("pass\n")

        if len(wrapped_fns) > 0:
            wrap_name = add_global("wrap", torch.fx.wrap)
            wrap_stmts = "\n".join([f'{wrap_name}("{name}")' for name in wrapped_fns])
        else:
            wrap_stmts = ""

        if self._body_transformer:
            body = self._body_transformer(body)

        for name, value in self.additional_globals():
            add_global(name, value)

        prologue = self._call_method_with_signature_check(
            self.gen_fn_def,
            free_vars,
            maybe_return_annotation[0],
            expanded_def=expanded_def,
        )

        # remove counter and generate lineno to node index mapping
        lineno_map: dict[int, int | None] = {}
        prologue_len = prologue.count("\n") + 1
        new_lines: list[str] = []
        cur_idx = None
        for line in "".join(body).split("\n"):
            counter = _counter_regexp.search(line)
            if counter is not None:
                cur_idx = int(counter.group(1))
            else:
                lineno_map[len(new_lines) + prologue_len] = cur_idx
                new_lines.append(line)

        code = "\n".join(new_lines).lstrip("\n")
        code = "\n".join("    " + line for line in code.split("\n"))

        fn_code = f"""
{wrap_stmts}

{prologue}
{code}"""
        # The +4 accounts for the empty lines before prologue in fn_code
        prologue_start = wrap_stmts.count("\n") + 4
        return PythonCode(
            fn_code,
            globals_,
            _lineno_map=lineno_map,
            _prologue_start=prologue_start,
        )