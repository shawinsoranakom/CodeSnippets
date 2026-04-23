def deserialize_outputs(self, serialized_node: Node, fx_node: torch.fx.Node):
        # Check single value return
        if len(serialized_node.outputs) == 0:
            return

        if (
            len(serialized_node.outputs) == 1
            and "torch.ops.higher_order" in serialized_node.target
            and not getattr(serialized_node, "is_hop_single_tensor_return", True)
            and serialized_node.outputs[0].type != "as_none"
        ):

            def _deserialize_hop_with_single_return(serialized_node, fx_node):
                meta_val: list[Any] = []
                arg = None
                if serialized_node.outputs[0].type == "as_tensor":
                    arg = serialized_node.outputs[0].as_tensor
                elif isinstance(
                    serialized_node.outputs[0].value,
                    (SymIntArgument, SymBoolArgument, SymFloatArgument),
                ):
                    arg = serialized_node.outputs[0].value
                deserialized_metadata = self.deserialize_metadata(
                    serialized_node.metadata
                )
                if arg is None:
                    raise AssertionError("arg should not be None")
                # pyrefly: ignore [bad-argument-type]
                self.generate_getitem(meta_val, fx_node, arg, 0, deserialized_metadata)
                fx_node.meta["val"] = tuple(meta_val)
                self.serialized_name_to_node[fx_node.name] = fx_node
                return

            return _deserialize_hop_with_single_return(serialized_node, fx_node)

        if (
            len(serialized_node.outputs) == 1
            and serialized_node.outputs[0].type == "as_tensor"
        ):
            self.sync_fx_node(serialized_node.outputs[0].as_tensor.name, fx_node)
            return
        elif len(serialized_node.outputs) == 1 and isinstance(
            serialized_node.outputs[0].value,
            (SymIntArgument, SymBoolArgument, SymFloatArgument),
        ):
            self.sync_fx_node(serialized_node.outputs[0].value.as_name, fx_node)
            return
        elif (
            len(serialized_node.outputs) == 1
            and serialized_node.outputs[0].type == "as_none"
        ):
            # manually rename the node to a unused name to avoid naming conflicts
            fx_node.meta["val"] = None
            fx_node._rename(f"{self.graph._target_to_str(fx_node.target)}_unused")
            return

        self.deserialize_multiple_outputs(serialized_node, fx_node)