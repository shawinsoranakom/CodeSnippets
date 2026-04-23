def operand_to_template_torchscript(self, op_id, oper, shape=None):
        """Return a TorchScript expression to build a template for a given operand."""
        if shape is None:
            shape = oper.shape
        else:
            if len(shape) != len(oper.shape):
                raise AssertionError(
                    f"shape length {len(shape)} != oper.shape length {len(oper.shape)}"
                )

        shape_parts = ["("]
        for d, s in enumerate(shape):
            if s > 0:
                # Fixed shape dimension: just add the value.
                shape_parts.append(str(s))
            elif s == 0:
                # Load time flexible shape dimension: it should have been computed in a variable.
                shape_parts.append(flex_name(op_id, d))
            elif s == -1:
                # Runtime flexible shape
                shape_parts.append("0")
            else:
                raise Exception(  # noqa: TRY002
                    "Unknown dim value, dimensions should be >= -1"
                )
            shape_parts.append(",")
        shape_parts.append(")")
        shape_code = "".join(shape_parts)
        if oper.op_type == NNAPI_OperandCode.TENSOR_FLOAT32:
            return f"torch.zeros({shape_code}, dtype=torch.float32)"
        elif oper.op_type == NNAPI_OperandCode.TENSOR_INT32:
            return f"torch.zeros({shape_code}, dtype=torch.int32)"
        elif oper.op_type == NNAPI_OperandCode.TENSOR_QUANT8_ASYMM:
            return (
                f"torch.quantize_per_tensor("
                f"torch.zeros(1), scale={oper.scale}, zero_point={oper.zero_point}, dtype=torch.quint8)"
                f".expand({shape_code}).contiguous()"
            )
        elif oper.op_type in (
            NNAPI_OperandCode.TENSOR_QUANT16_ASYMM,
            NNAPI_OperandCode.TENSOR_QUANT16_SYMM,
        ):
            if self.use_int16_for_qint16:
                return f"torch.zeros({shape_code}, dtype=torch.int16)"
            else:
                raise Exception(  # noqa: TRY002
                    "`int16` isn't supported. If you're trying to represent NNAPI"
                    " qint16 with Pytorch int16, set `use_int16_for_qint16 = True`"
                )

        raise Exception(  # noqa: TRY002
            f"Unsupported output operand type: {oper.op_type}"
        )