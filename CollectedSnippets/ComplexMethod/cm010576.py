def add_reshape(self, node):
        if node.inputsSize() != 2:
            raise AssertionError(
                f"expected node.inputsSize() == 2, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        in_id, in_oper = self.get_tensor_operand_by_jitval_fixed_size(node.inputsAt(0))

        shape_ctype, shape = self.get_constant_value(node.inputsAt(1))
        if shape_ctype.kind() != "ListType":
            raise AssertionError(
                f"expected shape_ctype ListType, got {shape_ctype.kind()}"
            )
        if shape_ctype.getElementType().kind() != "IntType":
            raise AssertionError(
                f"expected shape element type IntType, got {shape_ctype.getElementType().kind()}"
            )
        is_trivial_reshape = len(shape) == 2 and shape[1] == -1

        if in_oper.dim_order != DimOrder.PRESUMED_CONTIGUOUS and not is_trivial_reshape:
            raise Exception(  # noqa: TRY002
                "Currently, reshape is only supported on NHWC tensors if the target size is [X, -1]."
            )

        # Bit of a hack here.  Use a real tensor to infer the output shape.
        out_shape = torch.zeros(1).expand(in_oper.shape).reshape(shape).shape
        out_oper = in_oper._replace(
            shape=out_shape, dim_order=DimOrder.PRESUMED_CONTIGUOUS
        )

        inputs = [None] * 2
        inputs[0] = in_id
        inputs[1] = self.add_immediate_int_vector(shape)

        outputs = [None] * 1
        outputs[0] = self.add_tensor_operand(node.outputsAt(0), out_oper)

        self.add_operation(NNAPI_OperationCode.RESHAPE, inputs, outputs)