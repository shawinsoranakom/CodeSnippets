def run_node(self, node: Node) -> Any:
        self.node_counter += 1
        result = super().run_node(node)
        node.meta["fake_result"] = result
        node.meta["node_idx"] = self.node_counter

        # (1) Update metadata with the list of nodes that are used by this node
        # copy_() doesn't read from its first argument; it writes to it, overwriting previous data.
        # We don't want to treat it as "being used as an input".
        node_args = node.args
        if node.target is torch.ops.aten.copy_.default:
            node_args = node_args[1:]

        # (2) Update metadata to track aliasing information about view tensor nodes.
        if node.op == "call_function":
            view_type = _get_view_type(node.target)
            if view_type == _ViewType.SingleOutputView:
                if not isinstance(node.args[0], Node):
                    raise AssertionError(f"Expected Node, got {type(node.args[0])}")
                node.meta["view_of"] = node.args[0]
            elif view_type == _ViewType.MultiOutputView:
                self.multi_output_view_nodes[node] = node.args[0]

            # Check if we returned a multi-output view,
            # and we're now grabbing the individual views from the output.
            #
            # For multi-output views, we want to map each output view to the base,
            # but this mapping involves two separate nodes in FX IR.
            # e.g. "a, b = x_1.split(...)" becomes:
            #    %split_tensor : [num_users=2] = call_function[target=torch.ops.aten.split.Tensor](args = (%x_1, 2), kwargs = {})
            #    %getitem : [num_users=1] = call_function[target=operator.getitem](args = (%split_tensor, 0), kwargs = {})
            #    %getitem_1 : [num_users=1] = call_function[target=operator.getitem](args = (%split_tensor, 1), kwargs = {})
            # And we'd like to set:
            #    getitem1.meta['view_of'] = x_1
            elif node.target is _operator.getitem:
                list_arg = node.args[0]
                maybe_base_of_view = self.multi_output_view_nodes.get(list_arg, None)
                if maybe_base_of_view is not None:
                    # Note: we could also track indexing info here for multi-output views.
                    # I don't think this metadata is strictly needed for de-functionalization.
                    if not isinstance(maybe_base_of_view, Node):
                        raise AssertionError(
                            f"Expected Node, got {type(maybe_base_of_view)}"
                        )
                    node.meta["view_of"] = maybe_base_of_view

        if "view_of" in node.meta:
            # We're linking the current node with its first argument as views.
            # Assert here that this is actually the case, and their storages are the same.
            if not isinstance(node.meta["fake_result"], FakeTensor):
                raise AssertionError("Expected FakeTensor in fake_result")
            if not isinstance(node.meta["view_of"].meta["fake_result"], FakeTensor):
                raise AssertionError("Expected FakeTensor in view_of fake_result")
            view_storage = StorageWeakRef(node.meta["fake_result"]._typed_storage())
            base_storage = StorageWeakRef(
                node.meta["view_of"].meta["fake_result"]._typed_storage()
            )
            if view_storage != base_storage:
                raise AssertionError("view_storage != base_storage")
        return result