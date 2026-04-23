def _canonicalize_graph(
    sorted_inputs, sorted_outputs, graph, constants
) -> tuple[Graph, dict[str, str]]:
    def _get_argument(a: Argument):
        if a.type == "as_none":
            return None
        elif a.type == "as_tensor":
            return a.as_tensor
        elif a.type == "as_tensors":
            return a.as_tensors
        elif a.type == "as_int":
            return None
        elif a.type == "as_ints":
            return None
        elif a.type == "as_float":
            return None
        elif a.type == "as_floats":
            return None
        elif a.type == "as_string":
            return None
        elif a.type == "as_strings":
            return None
        elif a.type == "as_complex":
            return None
        elif a.type == "as_sym_int":
            return a.as_sym_int
        elif a.type == "as_sym_ints":
            return a.as_sym_ints
        elif a.type == "as_sym_float":
            return a.as_sym_float
        elif a.type == "as_sym_floats":
            return a.as_sym_floats
        elif a.type == "as_scalar_type":
            return None
        elif a.type == "as_memory_format":
            return None
        elif a.type == "as_layout":
            return None
        elif a.type == "as_device":
            return None
        elif a.type == "as_bool":
            return None
        elif a.type == "as_bools":
            return None
        elif a.type == "as_sym_bool":
            return a.as_sym_bool
        elif a.type == "as_sym_bools":
            return a.as_sym_bools
        elif a.type == "as_graph":
            return None
        elif a.type == "as_optional_tensors":
            return a.as_optional_tensors
        elif a.type == "as_custom_obj":
            return a.as_custom_obj
        elif a.type == "as_operator":
            return None
        elif a.type == "as_int_lists":
            return None
        elif a.type == "as_float_lists":
            return None
        elif a.type == "as_string_to_argument":
            return None
        elif a.type == "as_nested_tensors":
            return a.as_nested_tensors
        else:
            raise AssertionError(f"Unknown input type to the ExportedProgram: {a}")

    # Stage 1: Reorder named items.
    def for_args(f, a):
        if not isinstance(a, Argument):
            raise AssertionError(f"expected Argument, got {type(a).__name__}")
        pytree.tree_map(f, _get_argument(a))

    def sort_nodes(nodes):
        @dataclass
        class Edges:
            outs: list[int]
            ins: int

        graph_inputs: set[str] = set()
        def_table: dict[str, int] = {}
        edges: dict[int, Edges] = {}
        candidates: list[tuple[str, list[tuple[str, list[int]]], int]] = []
        rank: dict[str, int] = {}
        ret: list[Node] = []

        def get_name(a) -> str | None:
            if a is None:
                return None
            if isinstance(a, TensorArgument):
                return a.name
            elif isinstance(a, (SymIntArgument, SymBoolArgument, SymFloatArgument)):
                if a.type == "as_name":
                    return a.as_name
                elif a.type in ("as_int", "as_bool", "as_float"):
                    return None
                else:
                    raise AssertionError(f"Unknown argument type: {a}")
            elif isinstance(a, OptionalTensorArgument):
                if a.type == "as_tensor":
                    return a.as_tensor.name
                elif a.type == "as_none":
                    return None
                else:
                    raise AssertionError(f"Unknown optional tensor type: {a}")
            elif isinstance(a, CustomObjArgument):
                return a.name
            else:
                raise AssertionError(f"Unknown argument type: {a}")

        for i in sorted_inputs:

            def add_input(a):
                if s := get_name(a):
                    graph_inputs.add(s)

            for_args(add_input, i)

        for idx, node in enumerate(nodes):

            def add_def(a):
                if s := get_name(a):
                    if s in def_table:
                        raise AssertionError(f"symbol {s!r} already in def_table")
                    def_table[s] = idx

            for o in node.outputs:
                for_args(add_def, o)

            edges[idx] = Edges([], 0)

        for idx, user in enumerate(nodes):

            def add_edge(a):
                if s := get_name(a):
                    if s in constants:
                        return
                    if s not in def_table:
                        if s not in graph_inputs:
                            raise AssertionError(
                                f"symbol {s!r} not in def_table or graph_inputs"
                            )
                        return
                    src = def_table[s]
                    edges[src].outs.append(idx)
                    edges[idx].ins += 1

            for i in user.inputs:
                for_args(add_edge, i.arg)

        def add_rank(a):
            if s := get_name(a):
                if s in rank:
                    raise AssertionError(f"symbol {s!r} already in rank")
                rank[s] = len(rank)

        def get_rank(a):
            s = get_name(a)
            if s and s not in constants:
                return rank[s]
            else:
                return -1

        for i in sorted_inputs:
            for_args(add_rank, i)

        def add_candidate(idx: int):
            def get_ranks(i):
                ranks = []
                for_args(lambda x: ranks.append(get_rank(x)), i)
                return ranks

            node = nodes[idx]
            args_rank = [(a.name, get_ranks(a.arg)) for a in node.inputs]
            heapq.heappush(candidates, (node.target, args_rank, idx))

        for idx, e in edges.items():
            if e.ins == 0:
                add_candidate(idx)

        while len(candidates) > 0:
            _, _, idx = heapq.heappop(candidates)
            node = nodes[idx]
            for o in node.outputs:
                for_args(add_rank, o)
            ret.append(node)
            if idx not in edges:
                raise AssertionError(f"idx {idx} not in edges")
            for user in edges[idx].outs:
                e = edges[user]
                if e.ins <= 0:
                    raise AssertionError(f"e.ins should be > 0, got {e.ins}")
                e.ins -= 1
                if e.ins == 0:
                    add_candidate(user)
            edges[idx].outs.clear()

        return ret

    sorted_nodes = sort_nodes(graph.nodes)
    if len(sorted_nodes) != len(graph.nodes):
        raise AssertionError(
            f"expected {len(graph.nodes)} sorted nodes, got {len(sorted_nodes)}"
        )

    # Stage 2: Rename nodes.
    name_table: dict[str, str] = {}

    def rename_def(a):
        def _rename(arg_name, values):
            new_name = f"_{len(name_table)}"
            if arg_name in name_table:
                raise AssertionError(f"arg_name {arg_name!r} already in name_table")
            name_table[arg_name] = new_name
            if arg_name not in values:
                raise AssertionError(f"arg_name {arg_name!r} not in values")
            values[new_name] = values.pop(arg_name)
            return new_name

        if a is None:
            return
        if isinstance(a, TensorArgument):
            a.name = _rename(a.name, graph.tensor_values)
        elif isinstance(a, SymIntArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_int_values)
        elif isinstance(a, SymFloatArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_float_values)
        elif isinstance(a, SymBoolArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_bool_values)
        elif isinstance(a, CustomObjArgument):
            a.name = _rename(a.name, graph.custom_obj_values)
        else:
            raise AssertionError(f"Unknown argument type: {a}")

    def replace_use(a):
        if a is None:
            return
        if isinstance(a, TensorArgument):
            a.name = name_table.get(a.name, a.name)
        elif isinstance(a, (SymIntArgument, SymFloatArgument)):
            if a.type == "as_name":
                a.as_name = name_table.get(a.as_name, a.as_name)
        elif isinstance(a, SymBoolArgument):
            if a.type == "as_name":
                a.as_name = name_table.get(a.as_name, a.as_name)
        elif isinstance(a, OptionalTensorArgument):
            if a.type == "as_tensor":
                a.as_tensor.name = name_table.get(a.as_tensor.name, a.as_tensor.name)
        elif isinstance(a, CustomObjArgument):
            a.name = name_table.get(a.name, a.name)
        else:
            raise AssertionError(f"Unknown argument type: {a}")

    for i in sorted_inputs:
        for_args(rename_def, i)

    for n in sorted_nodes:
        for o in n.outputs:
            for_args(rename_def, o)

    for n in sorted_nodes:
        for i in n.inputs:
            for_args(replace_use, i.arg)

    for o in sorted_outputs:
        for_args(replace_use, o)

    # Stage 3: Remove unstable fields.
    for n in sorted_nodes:
        n.metadata.clear()

    # Stage 4: Aggregate values.
    # pyrefly: ignore [no-matching-overload]
    sorted_tensor_values = dict(
        sorted(graph.tensor_values.items(), key=operator.itemgetter(0))
    )
    # pyrefly: ignore [no-matching-overload]
    sorted_sym_int_values = dict(
        sorted(graph.sym_int_values.items(), key=operator.itemgetter(0))
    )
    # pyrefly: ignore [no-matching-overload]
    sorted_sym_float_values = dict(
        sorted(graph.sym_float_values.items(), key=operator.itemgetter(0))
    )
    # pyrefly: ignore [no-matching-overload]
    sorted_sym_bool_values = dict(
        sorted(graph.sym_bool_values.items(), key=operator.itemgetter(0))
    )
    # pyrefly: ignore [no-matching-overload]
    sorted_custom_obj_values = dict(
        sorted(graph.custom_obj_values.items(), key=operator.itemgetter(0))
    )

    # Stage 5: Recurse in subgraphs.
    counter = 0
    for node in sorted_nodes:
        for i in node.inputs:
            a = i.arg
            if a.type == "as_graph":
                a.as_graph.graph, _ = _canonicalize_graph(
                    a.as_graph.graph.inputs,
                    a.as_graph.graph.outputs,
                    a.as_graph.graph,
                    constants,
                )
                a.as_graph.name = f"_g{counter}"
                counter += 1

    graph = Graph(
        inputs=sorted_inputs,
        outputs=sorted_outputs,
        nodes=sorted_nodes,
        tensor_values=sorted_tensor_values,
        sym_int_values=sorted_sym_int_values,
        sym_float_values=sorted_sym_float_values,
        sym_bool_values=sorted_sym_bool_values,
        is_single_tensor_return=graph.is_single_tensor_return,
        custom_obj_values=sorted_custom_obj_values,
    )
    return graph, name_table