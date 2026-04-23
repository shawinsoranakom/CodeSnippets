def replace_with_graph(
        match: Match,
        graph: torch.fx.Graph,
        replacement_graph: torch.fx.Graph | torch.fx.GraphModule,
        args: Sequence[torch.fx.Node],
        pass_name: str | None = None,
    ) -> None:
        """
        Inserts the replacement graph into the toplevel graph at the match
        """

        added_replacement_nodes: list[torch.fx.Node] = []

        class Replacer(torch.fx.Interpreter):
            call_method = None  # type: ignore[assignment]
            call_module = None  # type: ignore[assignment]
            get_attr = None  # type: ignore[assignment]

            def run_node(self, node: torch.fx.Node) -> Any:
                if node.op in ("placeholder", "output"):
                    return super().run_node(node)
                target = node.target
                args, kwargs = self.fetch_args_kwargs_from_env(node)
                if node.op == "call_function":
                    assert callable(target)
                    result = graph.call_function(target, args, kwargs)
                    added_replacement_nodes.append(result)
                    _transfer_meta(
                        new_meta=result.meta,
                        old_node=node,
                        pass_name=pass_name or "",
                    )
                    # This function copy-pastes the replacement graph into
                    # the graph. If the replacement graph had any eager_input_vals,
                    # we propagate those over (val/tensor_meta are handled by
                    # _transfer_meta above).
                    if "eager_input_vals" in node.meta:
                        result.meta["eager_input_vals"] = node.meta["eager_input_vals"]
                    return result
                if node.op == "get_attr":
                    # If the replacement graph contains a HOP, the subgraphs of the HOP are "get_attr" nodes.
                    # We need to fetch the subgraph of the HOP then register the subgraph to the replaced graph's root.
                    from torch._higher_order_ops.utils import (
                        unique_graph_name_with_root,
                    )

                    sub_gm = super().get_attr(target, args, kwargs)
                    if not isinstance(sub_gm, torch.fx.GraphModule):
                        raise NotImplementedError(
                            f"NYI: replacement_graph.{target} is not a graph module. Got {sub_gm}."
                        )
                    assert graph.owning_module is not None
                    graph_name = None
                    for n, mod in graph.owning_module.named_modules():
                        if sub_gm is mod:
                            graph_name = n
                            break
                    if graph_name is None:
                        assert isinstance(target, str)
                        _, graph_name = unique_graph_name_with_root(
                            # pyrefly: ignore [unbound-name]
                            graph.owning_module,
                            target,
                        )
                        # pyrefly: ignore [unbound-name]
                        graph.owning_module.register_module(graph_name, sub_gm)
                    # pyrefly: ignore [unbound-name]
                    getattr_node = graph.get_attr(graph_name)
                    added_replacement_nodes.append(getattr_node)
                    return getattr_node

                raise NotImplementedError(f"unhandled {node}")

        output_nodes = match.output_nodes()

        if len(output_nodes) == 1:
            last_node = output_nodes[0]
        else:
            assert output_nodes[0]
            nodes = list(output_nodes[0].graph.nodes)
            indices = [
                (nodes.index(n), n)
                for n in output_nodes
                if isinstance(n, torch.fx.Node)
            ]
            last_node = min(indices, key=operator.itemgetter(0))[1]

        def percolate_tags(
            node: torch.fx.Node,
            tag_name: str,
            tag_value: str,
            input_stops: OrderedSet[torch.fx.Node],
        ) -> None:
            queue = [node]
            visited = OrderedSet[torch.fx.Node]()

            while queue:
                arg = queue.pop()
                if (
                    arg not in visited
                    and arg not in input_stops
                    and hasattr(arg, "meta")
                ):
                    visited.add(arg)
                    arg.meta[tag_name] = tag_value
                    queue.extend(arg.all_input_nodes)

        with graph.inserting_before(last_node):
            assert isinstance(replacement_graph, torch.fx.GraphModule)
            replacement = Replacer(replacement_graph).run(*args)
            if isinstance(replacement, torch.fx.Node):
                replacement = [replacement]

            def maybe_getitem(node: torch.fx.Node) -> Any:
                if node.op != "call_function":
                    return None
                if node.target != operator.getitem:
                    return None
                assert len(node.args) == 2
                return node.args[1]

            def replace(
                old: torch.fx.Node | None,
                new: torch.fx.Node | Sequence[torch.fx.Node] | None,
            ) -> None:
                def filter_nodes_in_newly_added_nodes(node: torch.fx.Node) -> bool:
                    # Do not replace the use of a node if it is being used by
                    # nodes in the replaced graph
                    return node not in added_replacement_nodes

                if old is None:
                    assert new is None
                    return
                assert isinstance(old, torch.fx.Node)
                if new is None:
                    old.replace_all_uses_with(
                        None,  # type: ignore[arg-type]
                        delete_user_cb=filter_nodes_in_newly_added_nodes,
                    )
                    if len(old.users) == 0:
                        graph.erase_node(old)
                    return
                if isinstance(new, torch.fx.Node):
                    _transfer_meta(new.meta, old, pass_name=pass_name or "")

                    # Preserve the recompute tags in the replacement graph. We
                    # look at the recompute tags of the original output node to
                    # propagate the tag from the output all the way to the input
                    # args (named as args in the replace_with_graph).
                    # Note that this is best effort. Since patterns are from
                    # many to many, there is no easy way to correctly map the
                    # recomputable tags. It is possible in some scenarios that we
                    # incorrectly tag some nodes as recomputables.
                    for tag_name in ["recompute", "ac_graph_id"]:
                        if tag_name in old.meta:
                            percolate_tags(
                                new, tag_name, old.meta[tag_name], OrderedSet(args)
                            )

                    old.replace_all_uses_with(
                        new, delete_user_cb=filter_nodes_in_newly_added_nodes
                    )
                    if len(old.users) == 0:
                        graph.erase_node(old)
                    return

                # `new` is not a node: it's a list of nodes.
                #
                # This happens when we want to replace a node that has a single
                # packed return with multiple unpacked returns. We need to do
                # some graph surgery here.
                #
                # Example:
                #   def original_graph(x):
                #      a = op(x)
                #      b = a[0]
                #      c = a[1]
                #      ...
                #
                # Assume that we want to replace op(x) with the graph
                #   def new_op(x):
                #      w = x + 1
                #      z = x + 2
                #      return (w, z)
                #
                # We need to replace `op` with the contents of `new_op`,
                # and then rewrite a[0] to be w and a[1] to be z, as so:
                #   def new_graph(x):
                #     w = x + 1
                #     z = x + 2
                #     b = w
                #     c = z
                #     ...
                old_uses = list(old.users.keys())
                for user in old_uses:
                    idx = maybe_getitem(user)
                    if idx is None:
                        # Output is used directly
                        # pyrefly: ignore [bad-argument-type]
                        old.replace_all_uses_with(new)
                    else:
                        replace(user, new[idx])
                graph.erase_node(old)

            if len(output_nodes) == len(replacement):
                for old, new in zip(output_nodes, replacement):
                    replace(old, new)
            else:
                assert len(output_nodes) == 1
                replace(output_nodes[0], replacement)

        match.erase_nodes()

        # Remove dead replacement nodes so they don't inflate user counts
        # in later lowering heuristics (e.g. should_realize_on_reuse).
        for node in reversed(added_replacement_nodes):
            if (
                not node.users
                and not node.is_impure()
                and not isinstance(node.target, torch._ops.HigherOrderOperator)
            ):
                graph.erase_node(node)