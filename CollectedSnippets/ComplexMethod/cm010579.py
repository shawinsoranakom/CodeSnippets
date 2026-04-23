def add_cat(self, node):
        if node.inputsSize() != 2:
            raise AssertionError(
                f"expected node.inputsSize() == 2, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        tensors = self.tensor_sequences[node.inputsAt(0)]
        _, dim = self.get_constant_value(node.inputsAt(1), "IntType")

        if len(tensors) <= 0:
            raise AssertionError(f"expected len(tensors) > 0, got {len(tensors)}")
        in_ids = []
        out_oper = None
        out_dim_size = 0
        for inp in tensors:
            in_id, in_oper = self.get_tensor_operand_by_jitval(inp)
            if out_oper is None:
                out_shape = change_element(in_oper.shape, dim, -1)
                out_oper = in_oper._replace(shape=out_shape)
            if in_oper.op_type != out_oper.op_type:
                raise AssertionError(
                    f"in_oper.op_type {in_oper.op_type} != out_oper.op_type {out_oper.op_type}"
                )
            if in_oper.dim_order != out_oper.dim_order:
                raise AssertionError(
                    f"in_oper.dim_order {in_oper.dim_order} != out_oper.dim_order {out_oper.dim_order}"
                )
            if change_element(in_oper.shape, dim, -1) != change_element(
                out_oper.shape, dim, -1
            ):
                raise AssertionError(
                    f"shape mismatch: {change_element(in_oper.shape, dim, -1)} != {change_element(out_oper.shape, dim, -1)}"
                )
            # TODO: Possibly check scale and zero point.
            in_ids.append(in_id)
            # TODO: Possibly support variable-sized inputs.
            out_dim_size += in_oper.shape[dim]

        if out_oper is None:
            raise AssertionError("out_oper must not be None")
        out_oper = out_oper._replace(
            shape=change_element(out_oper.shape, dim, out_dim_size)
        )

        if in_oper.dim_order == DimOrder.CHANNELS_LAST:  # type: ignore[possibly-undefined]
            if len(out_oper.shape) != 4:
                raise AssertionError(
                    f"expected len(out_oper.shape) == 4 for CHANNELS_LAST, got {len(out_oper.shape)}"
                )
            nnapi_dim = [0, 3, 1, 2][dim]
        else:
            nnapi_dim = dim

        out_id = self.add_tensor_operand(node.outputsAt(0), out_oper)
        for idx, d in enumerate(out_oper.shape):
            if d == 0:
                if idx == dim:
                    shape = " + ".join(flex_name(ip_id, dim) for ip_id in in_ids)
                    self.compute_operand_shape(out_id, idx, shape)
                else:
                    self.forward_operand_shape(out_id, idx, in_ids[0], idx)

        inputs = in_ids + [self.add_immediate_int_scalar(nnapi_dim)]

        outputs = [None] * 1
        outputs[0] = out_id

        self.add_operation(NNAPI_OperationCode.CONCATENATION, inputs, outputs)