def replace_node_output(self, node_id, index, new_value):
        node_id = self.prefix + node_id
        to_remove = []
        for node in self.nodes.values():
            for key, value in node.inputs.items():
                if is_link(value) and value[0] == node_id and value[1] == index:
                    if new_value is None:
                        to_remove.append((node, key))
                    else:
                        node.inputs[key] = new_value
        for node, key in to_remove:
            del node.inputs[key]