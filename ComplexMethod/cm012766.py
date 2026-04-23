def _apply_binary_op(a: CuteDSLArg, b: CuteDSLArg, op_format: str) -> CuteDSLArg:
        """
        Apply a binary operation with automatic scalar-to-tensor conversion.

        CuteDSL requires both operands to be TensorSSA objects for tensor operations.
        This helper automatically converts scalar arguments to TensorSSA using
        cute.full_like when at least one argument is a tensor (CSEVariable or OpsValue).

        Args:
            a: First operand (CSEVariable for tensors, str for scalars, or OpsValue wrapper)
            b: Second operand (CSEVariable for tensors, str for scalars, or OpsValue wrapper)
            op_format: Format string with {a} and {b} placeholders for the operation

        Returns:
            CSEVariable if at least one operand is a tensor, otherwise string
        """
        a_cse = CuteDSLOpOverrides._get_cse_var(a)
        b_cse = CuteDSLOpOverrides._get_cse_var(b)

        node_flags = CuteDSLOpOverrides._node_tensor_flags()
        if node_flags is not None:
            a_is_tensor, b_is_tensor = node_flags
        else:
            a_is_tensor = a_cse is not None
            b_is_tensor = b_cse is not None

        tensor_arg = a if a_is_tensor else (b if b_is_tensor else None)
        if tensor_arg is None:
            tensor_arg = a_cse or b_cse

        if tensor_arg is not None:
            if a_cse is None and b_cse is None:
                return op_format.format(
                    a=CuteDSLOpOverrides._as_expr(a),
                    b=CuteDSLOpOverrides._as_expr(b),
                )

            a_ssa = CuteDSLOpOverrides._ensure_tensor_ssa(
                a, tensor_arg, is_tensor=a_is_tensor
            )
            b_ssa = CuteDSLOpOverrides._ensure_tensor_ssa(
                b, tensor_arg, is_tensor=b_is_tensor
            )
            result_expr = op_format.format(a=a_ssa, b=b_ssa)

            dtype, bounds = CuteDSLOpOverrides._extract_dtype_and_bounds(a, b)
            expected = CuteDSLOpOverrides._expected_tensor_val()
            if dtype is None:
                dtype = expected.dtype if expected is not None else torch.int32
            if a_cse is not None:
                shape = a_cse.shape
            elif b_cse is not None:
                shape = b_cse.shape
            else:
                shape = tuple(expected.size()) if expected is not None else None

            # Create and return CSEVariable using CSE generation for caching
            return V.kernel.cse.generate(
                V.kernel.body, result_expr, bounds=bounds, dtype=dtype, shape=shape
            )

        return op_format.format(a=a, b=b)