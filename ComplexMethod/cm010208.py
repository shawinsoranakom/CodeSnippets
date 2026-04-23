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