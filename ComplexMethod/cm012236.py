def fuse(self, graph: torch.fx.GraphModule, subset: list[torch.fx.Node]):
        batch_inputs = []
        batch_weights = []
        batch_biases = []
        batch_nodes = []
        batch_inputs_meta = []
        batch_weights_meta = []
        batch_biases_meta = []

        for node in subset:
            if CallFunctionVarArgs(aten.addmm.default).match(node):
                bias, input, weight = node.args
            elif CallFunctionVarArgs(aten.mm.default).match(node):
                input, weight = node.args
                bias = None
            batch_nodes.append(node)
            batch_inputs.append(input)  # type: ignore[possibly-undefined]
            batch_weights.append(weight)  # type: ignore[possibly-undefined]
            batch_biases.append(bias)  # type: ignore[possibly-undefined]
            batch_inputs_meta.append(input.meta)  # type: ignore[possibly-undefined, union-attr]
            batch_weights_meta.append(weight.meta)  # type: ignore[possibly-undefined, union-attr]
            if bias is not None:  # type: ignore[possibly-undefined]
                batch_biases_meta.append(bias.meta)  # type: ignore[possibly-undefined, union-attr]
            else:
                batch_biases_meta.append(None)

        with graph.inserting_before(subset[-1]):  # type: ignore[operator]
            fused_inputs = decompose_stack(graph, batch_inputs)
            fused_weights = decompose_stack(graph, batch_weights)
            fused_inputs_meta_val = torch.stack(
                [input["val"] for input in batch_inputs_meta]
            )
            fused_weights_meta_val = torch.stack(
                [weight["val"] for weight in batch_weights_meta]
            )
            fused_bmm = graph.call_function(  # type: ignore[operator]
                aten.bmm,
                args=(fused_inputs, fused_weights),
            )
            fused_bmm.meta["val"] = aten.bmm(
                fused_inputs_meta_val, fused_weights_meta_val
            )
        for i, original_mm in enumerate(batch_nodes):
            has_bias = False
            with graph.inserting_after(fused_bmm):  # type: ignore[operator]
                new_mm = graph.call_function(aten.select, args=((fused_bmm, 0, i)))  # type: ignore[operator]
                new_mm.meta["val"] = aten.select(fused_bmm.meta["val"], 0, i)
                if batch_biases[i]:
                    has_bias = True
                    # broadcast the bias to the same shape as the mm output
                    if self.graph_search_options.get(
                        "shape_broadcast_batch_linear", False
                    ):
                        broadcast_shape = torch.broadcast_shapes(
                            batch_biases_meta[i]["val"].shape, new_mm.meta["val"].shape
                        )
                        broadcast_bias = graph.call_function(  # type: ignore[operator]
                            aten.broadcast_to.default,
                            args=(batch_biases[i],),
                            kwargs={"size": broadcast_shape},
                        )
                        broadcast_bias.meta["val"] = aten.broadcast_to(
                            batch_biases_meta[i]["val"], broadcast_shape
                        )  # type: ignore[assignment]
                        new_bias_add = graph.call_function(  # type: ignore[operator]
                            aten.add.Tensor, args=((broadcast_bias, new_mm))
                        )
                        new_bias_add.meta["val"] = aten.add.Tensor(
                            broadcast_bias.meta["val"], new_mm.meta["val"]
                        )
                    else:
                        new_bias_add = graph.call_function(  # type: ignore[operator]
                            aten.add, args=((batch_biases[i], new_mm))
                        )
                        new_bias_add.meta["val"] = aten.add.Tensor(
                            batch_biases_meta[i]["val"], new_mm.meta["val"]
                        )
            new_mm_cont = new_bias_add if has_bias else new_mm  # type: ignore[possibly-undefined]
            original_mm.replace_all_uses_with(new_mm_cont)
            new_mm_cont.meta.update(original_mm.meta)
            graph.erase_node(original_mm)  # type: ignore[operator]
        counters["inductor"]["batch_linear_post_grad"] += 1