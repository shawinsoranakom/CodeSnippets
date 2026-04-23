def serialize_hoo_outputs(self, node: torch.fx.Node) -> list[Argument]:
        """
        For serializing HOO outputs since HOOs do not have a schema.
        """
        meta_val = node.meta["val"]

        if isinstance(meta_val, tuple):
            outputs = []
            for i, element_meta_val in enumerate(meta_val):
                user_node = self._output_node_at_index(node, i)
                if isinstance(element_meta_val, list):
                    # e.g "-> Tensor[]"
                    tensors = []
                    for j, m in enumerate(element_meta_val):
                        if not isinstance(m, torch.Tensor):
                            raise SerializeError(
                                f"Serialize list output with type {type(m)} nyi"
                            )

                        if user_node is None:
                            name = f"{node.name}_unused_{i}_{j}"
                        else:
                            name = self._output_node_name_at_index(user_node, j)
                        tensors.append(self.serialize_tensor_output(name, m))
                    outputs.append(Argument.create(as_tensors=tensors))

                else:
                    name = (
                        user_node.name
                        if user_node is not None
                        else f"{node.name}_unused_{i}"
                    )

                    outputs.append(self.serialize_output(name, element_meta_val))

            return outputs
        elif isinstance(meta_val, dict):
            tensor_args = []
            # use the dict key as the idx
            for idx, meta in meta_val.items():
                if not isinstance(meta, torch.Tensor):
                    raise SerializeError(
                        f"Serialize list output with type {type(meta)} nyi"
                    )
                name = self._output_node_name_at_index(node, idx)
                tensor_args.append(self.serialize_tensor_output(name, meta))
            return [Argument.create(as_tensors=tensor_args)]
        else:
            return [self.serialize_output(node.name, meta_val)]