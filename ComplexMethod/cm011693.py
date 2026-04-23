def get_numel_rnumel(cls, node: BaseSchedulerNode) -> tuple[sympy.Expr, sympy.Expr]:
        if cls.is_split_reduction(node):
            xnumel = None
            rnumel = None
            for subnode in node.get_nodes():
                if not (
                    isinstance(subnode, SchedulerNode)
                    and subnode.is_reduction()
                    and isinstance(subnode.node, ComputedBuffer)
                ):
                    continue

                assert subnode.node._original_ranges is not None
                curxnumel = V.graph.sizevars.simplify(
                    sympy_product(subnode.node._original_ranges)
                )
                assert subnode.node._original_reduction_ranges is not None
                currnumel = V.graph.sizevars.simplify(
                    sympy_product(subnode.node._original_reduction_ranges)
                )

                if xnumel is None:
                    xnumel = curxnumel
                    rnumel = currnumel
                else:
                    assert V.graph.sizevars.statically_known_equals(
                        xnumel, curxnumel
                    ), f"{xnumel} v.s. {curxnumel}"
                    assert V.graph.sizevars.statically_known_equals(
                        rnumel, currnumel
                    ), f"{rnumel} v.s. {currnumel}"

            assert xnumel is not None
            return (xnumel, rnumel)
        else:
            return node.group[1]