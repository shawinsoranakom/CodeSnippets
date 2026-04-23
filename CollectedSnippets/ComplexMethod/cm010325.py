def finalize_outputs(self):
        self.created_modules.pop(self.fqn, None)

        orig_outputs = []

        signature = self.module_call_graph.get(self.child_fqn)
        if signature is not None and self.parent is not None:
            for output in signature.outputs:
                if isinstance(
                    output,
                    (
                        TensorArgument,
                        SymIntArgument,
                        SymBoolArgument,
                        SymFloatArgument,
                        ConstantArgument,
                    ),
                ):
                    if output.name in self.seen_nodes:
                        orig_outputs.append(self.seen_nodes[output.name])
                    else:
                        orig_outputs.append(None)
                else:
                    raise RuntimeError(
                        f"Unsupported data type for output node: {output}"
                    )

            def get_actual_output_node(output):
                if output is None:
                    return None

                seen_node = self.seen_nodes[output.name]
                if seen_node in self.node_map:
                    return self.node_map[seen_node]
                elif seen_node in self.node_to_placeholder:
                    return self.node_to_placeholder[seen_node]
                else:
                    raise RuntimeError(
                        f"Could not find output node {output}. Graph: {self.graph}"
                    )

            tree_out_node = _generate_unflatten(
                self.module,
                tuple(get_actual_output_node(output) for output in orig_outputs),
                signature.out_spec,
            )
            parent_out: torch.fx.Node | None = _generate_flatten_spec(
                self.parent.module, self.parent_call_module, signature.out_spec
            )
            graph_outputs: torch.fx.Node | list[torch.fx.Node] = tree_out_node
        else:
            graph_outputs = []
            # Iterate through nodes we have copied into self.graph.
            for orig_node in self.node_map:
                for user_node in orig_node.users:
                    if user_node.name not in self.seen_nodes:
                        # external user node, need to expose as an output
                        orig_outputs.append(orig_node)
                        graph_outputs.append(self.node_map[orig_node])
                        break

            parent_out = self.parent_call_module
            if len(graph_outputs) == 1:
                graph_outputs = graph_outputs[0]

        if not isinstance(graph_outputs, (list, torch.fx.Node)):
            raise AssertionError(
                f"expected graph_outputs to be list or torch.fx.Node, got {type(graph_outputs)}"
            )

        self.graph.output(graph_outputs)

        # Rewrite outputs in parent module
        if parent_out is None:
            return

        parent_out.meta["val"] = (
            graph_outputs.meta.get("val")
            if isinstance(graph_outputs, torch.fx.Node)
            else [o.meta.get("val") for o in graph_outputs]
        )
        self.uplift_common_custom_metadata()

        if len(orig_outputs) == 1 and signature is None:
            self.parent.node_map[orig_outputs[0]] = parent_out
        else:
            for i, orig_output in enumerate(orig_outputs):
                if orig_output is None:
                    continue
                # Use Proxy to record getitem access.
                proxy_out = torch.fx.Proxy(parent_out)[i].node  # type: ignore[index]
                proxy_out.meta["val"] = orig_output.meta.get("val")
                self.parent.node_map[orig_output] = proxy_out