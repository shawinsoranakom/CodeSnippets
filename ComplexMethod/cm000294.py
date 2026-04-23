def derivative(self, param: Variable, operation: Operation) -> np.ndarray:
        """
        Compute the derivative of given operation/function

        Args:
            param: variable to be differentiated
            operation: function performed on the input variable

        Returns:
            Derivative of input variable with respect to the output of
            the operation
        """
        params = operation.params

        if operation == OpType.ADD:
            return np.ones_like(params[0].to_ndarray(), dtype=np.float64)
        if operation == OpType.SUB:
            if params[0] == param:
                return np.ones_like(params[0].to_ndarray(), dtype=np.float64)
            return -np.ones_like(params[1].to_ndarray(), dtype=np.float64)
        if operation == OpType.MUL:
            return (
                params[1].to_ndarray().T
                if params[0] == param
                else params[0].to_ndarray().T
            )
        if operation == OpType.DIV:
            if params[0] == param:
                return 1 / params[1].to_ndarray()
            return -params[0].to_ndarray() / (params[1].to_ndarray() ** 2)
        if operation == OpType.MATMUL:
            return (
                params[1].to_ndarray().T
                if params[0] == param
                else params[0].to_ndarray().T
            )
        if operation == OpType.POWER:
            power = operation.other_params["power"]
            return power * (params[0].to_ndarray() ** (power - 1))

        err_msg = f"invalid operation type: {operation.op_type}"
        raise ValueError(err_msg)