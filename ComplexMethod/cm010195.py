def deserialize_graph_output(self, output) -> torch.fx.Node | int | None:
        if output.type == "as_tensor":
            return self.serialized_name_to_node[output.as_tensor.name]
        elif output.type == "as_sym_int":
            return self.serialized_name_to_node[output.as_sym_int.as_name]
        elif output.type == "as_sym_bool":
            return self.serialized_name_to_node[output.as_sym_bool.as_name]
        elif output.type == "as_sym_float":
            return self.serialized_name_to_node[output.as_sym_float.as_name]
        elif output.type == "as_int":
            return output.as_int
        elif output.type == "as_float":
            return output.as_float
        elif output.type == "as_bool":
            return output.as_bool
        elif output.type == "as_none":
            return None
        else:
            raise SerializeError(f"Unable to deserialize output node {output}")