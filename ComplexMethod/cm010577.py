def add_flatten(self, node):
        if node.inputsSize() != 3:
            raise AssertionError(
                f"expected node.inputsSize() == 3, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        in_id, in_oper = self.get_tensor_operand_by_jitval(node.inputsAt(0))

        _start_ctype, start_dim = self.get_constant_value(node.inputsAt(1), "IntType")
        _end_ctype, end_dim = self.get_constant_value(node.inputsAt(2), "IntType")

        # channels last with channels == 1 or (height & width both 1)
        is_trivial_flatten = len(in_oper.shape) == 4 and (
            in_oper.shape[1] == 1 or (in_oper.shape[2] == 1 and in_oper.shape[3] == 1)
        )
        if in_oper.dim_order != DimOrder.PRESUMED_CONTIGUOUS and not is_trivial_flatten:
            raise Exception(  # noqa: TRY002
                "Currently, flatten is not supported on NHWC tensors unless C=1 or H=W=1"
            )

        if start_dim < 0:
            start_dim += len(in_oper.shape)
        if end_dim < 0:
            end_dim += len(in_oper.shape)

        out_shape = (
            in_oper.shape[:start_dim]
            + (functools.reduce(operator.mul, in_oper.shape[start_dim : end_dim + 1]),)
            + in_oper.shape[end_dim + 1 :]
        )

        if any(dim == 0 for dim in in_oper.shape[start_dim : end_dim + 1]):
            raise Exception(  # noqa: TRY002
                "Flattening flexible dims is not supported yet"
            )
        non_flattened_dims = in_oper.shape[:start_dim] + in_oper.shape[end_dim + 1 :]
        if non_flattened_dims.count(0) > 1:
            raise Exception("Only 1 dim can be flexible")  # noqa: TRY002

        out_oper = in_oper._replace(
            shape=out_shape, dim_order=DimOrder.PRESUMED_CONTIGUOUS
        )
        out_id = self.add_tensor_operand(node.outputsAt(0), out_oper)

        for idx, dim in enumerate(out_shape):
            if dim == 0:
                self.forward_operand_shape(out_id, idx, in_id, in_oper.shape.index(0))

        inputs_1 = tuple(dim if dim != 0 else -1 for dim in out_shape)
        inputs = [None] * 2
        inputs[0] = in_id
        inputs[1] = self.add_immediate_int_vector(inputs_1)

        outputs = [None] * 1
        outputs[0] = out_id

        self.add_operation(NNAPI_OperationCode.RESHAPE, inputs, outputs)