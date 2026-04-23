def backward(ctx, D_grad, U_grad):  # pyrefly: ignore  # bad-override
        A_grad = B_grad = None
        grads = [None] * 14

        A, B, D, U = ctx.saved_tensors
        largest = ctx.largest

        # lobpcg.backward has some limitations. Checks for unsupported input
        if A.is_sparse or (B is not None and B.is_sparse and ctx.needs_input_grad[2]):
            raise ValueError(
                "lobpcg.backward does not support sparse input yet."
                "Note that lobpcg.forward does though."
            )
        if (
            A.dtype in (torch.complex64, torch.complex128)
            or B is not None
            and B.dtype in (torch.complex64, torch.complex128)
        ):
            raise ValueError(
                "lobpcg.backward does not support complex input yet."
                "Note that lobpcg.forward does though."
            )
        if B is not None:
            raise ValueError(
                "lobpcg.backward does not support backward with B != I yet."
            )

        if largest is None:
            largest = True

        # symeig backward
        if B is None:
            A_grad = _symeig_backward(D_grad, U_grad, A, D, U, largest)

        # A has index 0
        grads[0] = A_grad
        # B has index 2
        grads[2] = B_grad
        return tuple(grads)