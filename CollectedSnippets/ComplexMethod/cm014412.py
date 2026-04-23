def populate_namespace_from_OP_to_IO(self) -> None:
        for node in self.nodes_op:
            for node_output, outputSize in zip(node.outputs, node.outputstensor_size, strict=True):
                self.scope_name_appeared.append(node.scopeName)
                self.nodes_io[node_output] = NodeBase(
                    node_output,
                    node.inputs,
                    node.scopeName,
                    outputSize,
                    op_type=node.kind,
                    attributes=node.attributes,
                )

        self.find_common_root()

        for node in self.nodes_op:
            for input_node_id in node.inputs:
                self.unique_name_to_scoped_name[input_node_id] = (
                    node.scopeName + "/" + input_node_id
                )

        for key, node in self.nodes_io.items():
            if type(node) is NodeBase:
                # pyrefly: ignore [unsupported-operation]
                self.unique_name_to_scoped_name[key] = node.scope + "/" + node.debugName
            if hasattr(node, "input_or_output"):
                self.unique_name_to_scoped_name[key] = (
                    node.input_or_output + "/" + node.debugName
                )

            if hasattr(node, "scope") and node.scope is not None:
                self.unique_name_to_scoped_name[key] = node.scope + "/" + node.debugName
                if node.scope == "" and self.shallowest_scope_name:
                    self.unique_name_to_scoped_name[node.debugName] = (

                        self.shallowest_scope_name + "/" + node.debugName
                    )

        # replace name
        for key, node in self.nodes_io.items():
            self.nodes_io[key].inputs = [
                self.unique_name_to_scoped_name[node_input_id]
                for node_input_id in node.inputs
            ]
            if node.debugName in self.unique_name_to_scoped_name:
                self.nodes_io[key].debugName = self.unique_name_to_scoped_name[
                    node.debugName
                ]