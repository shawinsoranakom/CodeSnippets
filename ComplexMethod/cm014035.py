def has_aliasing(self) -> AliasingInfo:
        from torch._dynamo.variables.higher_order_ops import get_tensor_storages
        from torch._higher_order_ops.utils import _collect_fake_inputs

        input_storages: dict[StorageWeakRef, torch.fx.Node] = dict()

        for node in self.graph.nodes:
            if node.op == "placeholder":
                example_value = _collect_fake_inputs([node])[0]
                if isinstance(example_value, torch.Tensor):
                    for storage in get_tensor_storages(example_value):
                        if storage in input_storages:
                            # input-input aliasing
                            msg = f"Input-to-input aliasing detected at nodes {input_storages[storage]} and {node}"
                            return AliasingInfo(True, msg)
                        input_storages[storage] = node
            else:
                break

        output_storages: dict[StorageWeakRef, torch.fx.Node] = dict()
        out_nodes = self.graph.find_nodes(op="output")[0]
        for out_node in pytree.tree_leaves(out_nodes.args[0]):
            if out_node:
                example_value = _collect_fake_inputs([out_node])[0]
                assert not isinstance(example_value, list)
                if isinstance(example_value, torch.Tensor):
                    for storage in get_tensor_storages(example_value):
                        if storage in output_storages:
                            # output-output aliasing
                            msg = f"Output-to-output aliasing detected at nodes {output_storages[storage]} and {out_node}"
                            return AliasingInfo(True, msg)
                        output_storages[storage] = out_node

        intersected_storages = input_storages.keys() & output_storages.keys()
        if len(intersected_storages) > 0:
            # input-output aliasing
            aliased = [
                (input_storages[s], output_storages[s]) for s in intersected_storages
            ]
            aliased = ", ".join([f"{i} and {o}" for i, o in aliased])
            msg = f"Input-to-output aliasing detected at nodes {aliased}"
            return AliasingInfo(True, msg)

        return AliasingInfo(False, "")