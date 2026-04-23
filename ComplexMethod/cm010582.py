def add_prelu_op(self, node):
        if node.inputsSize() != 2:
            raise AssertionError(
                f"expected node.inputsSize() == 2, got {node.inputsSize()}"
            )
        if node.outputsSize() != 1:
            raise AssertionError(
                f"expected node.outputsSize() == 1, got {node.outputsSize()}"
            )

        if node.inputsAt(0).type().kind() != "TensorType":
            raise AssertionError(
                f"expected inputsAt(0) TensorType, got {node.inputsAt(0).type().kind()}"
            )
        if node.inputsAt(1).type().kind() != "TensorType":
            raise AssertionError(
                f"expected inputsAt(1) TensorType, got {node.inputsAt(1).type().kind()}"
            )

        in_id, in_oper = self.get_tensor_operand_by_jitval(node.inputsAt(0))
        w_id, w_oper = self.get_tensor_operand_for_weight(node.inputsAt(1))
        if len(w_oper.shape) != 1:
            raise AssertionError(
                f"expected len(w_oper.shape) == 1, got {len(w_oper.shape)}"
            )
        if w_oper.shape[0] <= 0:
            raise AssertionError(f"expected w_oper.shape[0] > 0, got {w_oper.shape[0]}")
        if w_oper.shape[0] > 1:
            if in_oper.use_nchw():
                # TODO: Support this by adding trailing 1 dims.
                raise Exception(  # noqa: TRY002
                    "Per-channel PReLU only supports channels_last right now."
                )

        out_id = self.add_tensor_operand(node.outputsAt(0), in_oper)
        for dim, size in enumerate(in_oper.shape):
            if size > 0:
                pass
            elif dim <= 1:
                raise Exception(  # noqa: TRY002
                    "PReLU requires fixed size for dim 0 and dim 1."
                )
            else:
                self.forward_operand_shape(out_id, dim, in_id, dim)

        inputs = [None] * 2
        inputs[0] = in_id
        inputs[1] = w_id

        outputs = [None] * 1
        outputs[0] = out_id

        self.add_operation(NNAPI_OperationCode.PRELU, inputs, outputs)