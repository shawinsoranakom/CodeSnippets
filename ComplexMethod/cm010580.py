def add_mean(self, node):
        if node.inputsSize() != 4:
            raise AssertionError(
                f"expected node.inputsSize() == 4, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        in_id, in_oper = self.get_tensor_operand_by_jitval_fixed_size(node.inputsAt(0))
        dim_ctype, dim = self.get_constant_value(node.inputsAt(1))
        if dim_ctype.kind() != "ListType":
            raise AssertionError(f"expected dim_ctype ListType, got {dim_ctype.kind()}")
        if dim_ctype.getElementType().kind() != "IntType":
            raise AssertionError(
                f"expected dim element type IntType, got {dim_ctype.getElementType().kind()}"
            )
        _, keep_dim = self.get_constant_value(node.inputsAt(2), "BoolType")
        # Expect None for dtype
        self.get_constant_value(node.inputsAt(3), "NoneType")

        if in_oper.dim_order == DimOrder.CHANNELS_LAST:
            if len(in_oper.shape) != 4:
                raise AssertionError(
                    f"expected len(in_oper.shape) == 4 for CHANNELS_LAST, got {len(in_oper.shape)}"
                )
            nnapi_dim = [[0, 3, 1, 2][d] for d in dim]
        else:
            nnapi_dim = dim

        collapsed_dims = set()
        for d in dim:
            if d < 0:
                d += len(in_oper.shape)
            collapsed_dims.add(d)

        if in_oper.dim_order == DimOrder.CHANNELS_LAST and not keep_dim:
            if not collapsed_dims.issuperset({2, 3}):
                raise AssertionError(
                    f"expected collapsed_dims to include {{2, 3}}, got {collapsed_dims}"
                )
            out_dim_order = DimOrder.PRESUMED_CONTIGUOUS
        else:
            out_dim_order = in_oper.dim_order

        out_shape = []
        for i, s in enumerate(in_oper.shape):
            if i not in collapsed_dims:
                out_shape.append(s)
            elif keep_dim:
                out_shape.append(1)

        out_oper = in_oper._replace(shape=out_shape, dim_order=out_dim_order)

        inputs = [None] * 3
        inputs[0] = in_id
        inputs[1] = self.add_immediate_int_vector(nnapi_dim)
        inputs[2] = self.add_immediate_int_scalar(keep_dim)

        outputs = [None] * 1
        outputs[0] = self.add_tensor_operand(node.outputsAt(0), out_oper)

        self.add_operation(NNAPI_OperationCode.MEAN, inputs, outputs)