def deserialize_graph(self, serialized_graph: Graph) -> torch.fx.Graph:
        log.debug("\n[deserialize_graph]")

        # Handle the tensor metas.
        for name, tensor_value in serialized_graph.tensor_values.items():
            log.debug("[deserialize_tensor_meta] %s (input): %s", name, tensor_value)
            self.serialized_name_to_meta[name] = (
                lambda v=tensor_value: self.deserialize_tensor_meta(v)
            )

        for name, sym_int_value in serialized_graph.sym_int_values.items():
            log.debug("[deserialize_sym_int] %s (input): %s", name, sym_int_value)
            self.serialized_name_to_meta[name] = (
                lambda v=sym_int_value: self.deserialize_sym_int(v)
            )

        for name, sym_float_value in serialized_graph.sym_float_values.items():
            log.debug("[deserialize_sym_float] %s (input): %s", name, sym_float_value)
            self.serialized_name_to_meta[name] = (
                lambda v=sym_float_value: self.deserialize_sym_float(v)
            )

        for name, sym_bool_value in serialized_graph.sym_bool_values.items():
            log.debug("[deserialize_sym_bool] %s (input): %s", name, sym_bool_value)
            self.serialized_name_to_meta[name] = (
                lambda v=sym_bool_value: self.deserialize_sym_bool(v)
            )

        for name, script_obj_meta in serialized_graph.custom_obj_values.items():
            log.debug("[deserialize_script_obj_meta] %s", script_obj_meta)
            self.serialized_name_to_meta[name] = (
                lambda v=script_obj_meta: self.deserialize_script_obj_meta(v)
            )

        log.debug("\n[deserialize graph nodes]")
        # Inputs: convert to placeholder nodes in FX.
        for i, input_ in enumerate(serialized_graph.inputs):
            log.debug("[deserialize input] %s", input_)
            if input_.type in ("as_tensor", "as_custom_obj"):
                node_name = input_.value.name
                placeholder_node = self.graph.placeholder(node_name)
                # FX might declare a name illegal (e.g. some nn.Modules use "input" as forward() arguments)
                # we will overwrite it
                placeholder_node.name = node_name
                self.sync_fx_node(node_name, placeholder_node)
            elif input_.type == "as_sym_int":
                if input_.value.type == "as_name":
                    node_name = input_.value.as_name
                    placeholder_node = self.graph.placeholder(node_name)
                    # FX might declare a name illegal (e.g. some nn.Modules use "input" as forward() arguments)
                    # we will overwrite it
                    placeholder_node.name = node_name
                    self.sync_fx_node(node_name, placeholder_node)
                else:
                    raise SerializeError(
                        f"Deserializing a constant symint {input_.value} as an input"
                    )
            elif input_.type in (
                "as_int",
                "as_float",
                "as_bool",
                "as_none",
                "as_string",
            ):
                node_name = self.signature.input_specs[i].arg.name or f"arg{i}"
                placeholder_node = self.graph.placeholder(node_name)
                placeholder_node.meta["val"] = self.deserialize_input(input_)
            else:
                raise SerializeError(f"Invalid input type {input_}")

        # Nodes: convert to call_function nodes.
        for serialized_node in serialized_graph.nodes:
            try:
                target = self.deserialize_operator(serialized_node.target)
                self.deserialize_node(serialized_node, target)

            except Exception as e:
                raise SerializeError(
                    f"Failed deserializing node {serialized_node}\n Original exception {traceback.format_exc()}"
                ) from e

        # Outputs: convert to a single `output` node.
        outputs = []
        for output in serialized_graph.outputs:
            log.debug("[deserialize output] %s", output)
            outputs.append(self.deserialize_graph_output(output))

        if serialized_graph.is_single_tensor_return:
            if len(outputs) != 1:
                raise AssertionError(
                    f"expected single output for single_tensor_return, got {len(outputs)}"
                )
            outputs = outputs[0]  # type: ignore[assignment]
        else:
            outputs = tuple(outputs)  # type: ignore[assignment]

        output_node = self.graph.output(outputs)

        if serialized_graph.is_single_tensor_return:
            output_node.meta["val"] = output_node.args[0].meta["val"]
        else:
            output_node.meta["val"] = tuple(
                arg.meta["val"] if isinstance(arg, torch.fx.Node) else arg
                for arg in output_node.args[0]
            )

        # recompute unbacked bindings
        for node in self.graph.nodes:
            if (val := node.meta.get("val")) is not None and (
                unbacked_bindings := symbolic_shapes._free_unbacked_symbols_with_path(
                    val,
                    (),
                    shape_env=self.shape_env,
                    pending=self.unbacked_symbols,
                    simplify=True,
                )
            ):
                node.meta["unbacked_bindings"] = unbacked_bindings

        if len(self.unbacked_symbols) != 0:
            raise AssertionError(
                f"expected no unbacked symbols, got {len(self.unbacked_symbols)}: {self.unbacked_symbols}"
            )
        return self.graph