def _dfs_get_attr(block):
            for node in block.nodes():
                if node.kind() == "prim::CreateObject":
                    output_name = node.output().debugName()
                    name_to_attribute_fqn[output_name] = ""

                if node.kind() == "prim::GetAttr":
                    attr_fqn = get_fqn(node)
                    value = get_attr(attr_fqn)
                    output_name = node.output().debugName()
                    name_to_attribute_fqn[output_name] = attr_fqn
                    if isinstance(value, torch.Tensor):
                        if attr_fqn not in self.name_to_buffer:
                            # Lift tensor constants to be a buffer
                            self.name_to_buffer[attr_fqn] = value
                    elif isinstance(value, torch.ScriptObject):
                        if attr_fqn not in self.name_to_constant:
                            self.name_to_constant[attr_fqn] = value
                    else:
                        self.name_to_non_tensor_attributes[attr_fqn] = value

                for subblock in node.blocks():
                    _dfs_get_attr(subblock)