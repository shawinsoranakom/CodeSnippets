def merge_mm_shared_rhs(graph: fx.Graph):
            """
            Bad POC of merging mm with a shared RHS.
            i.e. [mm(x, W), mm(x2, W)] => mm(cat(x, x2), W).split()

            Isn't actually safe for a couple reasons. For example, it doesn't handle the
            case where the LHS inputs depend on each other
            """
            saved_graph[0] = graph
            matmuls = [n for n in graph.nodes if n.target == torch.mm]
            rhs_vals = defaultdict(set)
            for m in matmuls:
                rhs_vals[m.args[1]].add(m)

            order = {n: idx for idx, n in enumerate(graph.nodes)}

            for rhs, matmuls in rhs_vals.items():
                if len(matmuls) == 1:
                    continue
                matmuls = sorted(matmuls, key=lambda x: order[x])
                with graph.inserting_before(matmuls[0]):
                    lhs_vals = [m.args[0] for m in matmuls]
                    new_cat = graph.create_node(
                        "call_function", torch.cat, args=(lhs_vals, 0)
                    )
                    new_mm = graph.create_node(
                        "call_function", torch.mm, args=(new_cat, rhs)
                    )
                    split_vals = graph.create_node(
                        "call_function",
                        torch.split,
                        args=(
                            new_mm,
                            [l.meta["example_value"].shape[0] for l in lhs_vals],
                        ),
                    )
                for idx, m in enumerate(matmuls):
                    m.target = operator.getitem
                    m.args = (split_vals, idx)