def serialize_model(self, model, inputs, return_shapes=None):
        self.add_immediate_bool_scalar(False)
        self.add_immediate_bool_scalar(True)

        inp_dim_orders = []
        out_dim_orders = []

        self_jitval = next(model.graph.inputs())
        self.add_constant_value(self_jitval, self_jitval.type(), model)

        for arg_idx, (input_value, input_tensor) in enumerate(
            zip(list(model.graph.inputs())[1:], inputs)
        ):
            op_id = self.add_tensor_operand_for_input(
                arg_idx, input_value, input_tensor
            )
            inp_dim_orders.append(self.operands[op_id].dim_order.value)

        for idx, node in enumerate(model.graph.nodes()):
            LOG.debug("Processing node #%d: %r", idx, node)
            self.add_node(node)

        retn = model.graph.return_node()
        if retn.inputsSize() != 1:
            raise AssertionError(
                f"expected retn.inputsSize() == 1, got {retn.inputsSize()}"
            )
        if retn.outputsSize() != 0:
            raise AssertionError(
                f"expected retn.outputsSize() == 0, got {retn.outputsSize()}"
            )
        retn_input = retn.inputsAt(0)
        template_return_lines = ["return ["]
        if retn_input.type().kind() == "TensorType":
            return_values = [retn_input]
            retval_count = -1
        elif retn_input.type().kind() == "TupleType":
            return_values = self.tensor_sequences[retn_input]
            retval_count = len(return_values)
        else:
            raise Exception(  # noqa: TRY002
                f"Unsupported return type: {retn_input.type()}"
            )

        if return_shapes is not None:
            if len(return_shapes) != len(return_values):
                raise AssertionError(
                    f"return_shapes length {len(return_shapes)} != return_values length {len(return_values)}"
                )
        for i, v in enumerate(return_values):
            op_id = self.jitval_operand_map[v]
            self.outputs.append(op_id)
            out_dim_orders.append(self.operands[op_id].dim_order.value)
            shape = return_shapes[i] if return_shapes else None
            template_return_lines.append(
                self.operand_to_template_torchscript(op_id, self.operands[op_id], shape)
                + ","
            )
        template_return_lines.append("]")

        model = []

        version = 1
        header = struct.pack(
            "iiiiii",
            version,
            len(self.operands),
            len(self.values),
            len(self.operations),
            len(self.inputs),
            len(self.outputs),
        )
        model.append(header)

        serialized_values, serialized_value_data = self.serialize_values()

        model.extend(
            struct.pack("iifi", t, len(d), s, z) for (t, d, _m, s, z) in self.operands
        )
        model.extend(serialized_values)
        model.extend(struct.pack("iii", *x) for x in self.operations)

        # Compact the model so we can get its length so far.
        model = [b"".join(model)]
        model_offset = len(model[0])
        # Model offset is the index into the model (in 32-bit words, not bytes)
        # of the next dimension we're about to serialize.  If it's 0,
        # generate code to mutate it before passing to NNAPI.
        if model_offset % 4 != 0:
            raise AssertionError(
                f"model_offset must be divisible by 4, got {model_offset}"
            )
        model_offset = int(model_offset / 4)

        for op_id, (_, dims, dim_order, _, _) in enumerate(self.operands):
            shape = fix_shape(dims, dim_order)
            for d, s in enumerate(shape):
                if s == 0:
                    pt_d = reverse_map_dim(dim_order, d)
                    self.flexible_shape_computation_lines.append(
                        f"ser_model[{model_offset}] = {flex_name(op_id, pt_d)}"
                    )
                model_offset += 1

            # convert runtime flex shape from -1 to 0
            shape = tuple(d if d != -1 else 0 for d in shape)
            model.append(self.serialize_ints(shape))

        model.extend(serialized_value_data)
        model.append(self.serialize_ints(self.operation_args))
        model.append(self.serialize_ints(self.inputs))
        model.append(self.serialize_ints(self.outputs))

        self.flexible_shape_computation_lines.extend(template_return_lines)

        return (
            array.array("i", b"".join(model)),
            self.used_weights,
            inp_dim_orders,
            out_dim_orders,
            self.flexible_shape_computation_lines,
            retval_count,
        )