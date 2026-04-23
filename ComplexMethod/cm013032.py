def addmm(g: jit_utils.GraphContext, self, mat1, mat2, beta, alpha):
    scalar_type = None
    self_scalar_type = symbolic_helper._try_get_scalar_type(self)
    mat1_scalar_type = symbolic_helper._try_get_scalar_type(mat1)
    mat2_scalar_type = symbolic_helper._try_get_scalar_type(mat2)
    if self_scalar_type is not None:
        scalar_type = self_scalar_type
    elif mat1_scalar_type is not None:
        scalar_type = mat1_scalar_type
    elif mat2_scalar_type is not None:
        scalar_type = mat2_scalar_type

    mat1_rank = symbolic_helper._get_tensor_rank(mat1)
    mat2_rank = symbolic_helper._get_tensor_rank(mat2)

    def is_not_none_nor(v, u):
        return v is not None and v != u

    if scalar_type is not None and (
        is_not_none_nor(mat1_rank, 2) or is_not_none_nor(mat2_rank, 2)
    ):
        res1 = g.op("MatMul", mat1, mat2)
        res2 = self

        alpha = symbolic_helper._scalar(alpha)
        beta = symbolic_helper._scalar(beta)

        if alpha != 1:
            alpha = g.op(
                "Constant", value_t=torch.tensor(alpha, dtype=scalar_type.dtype())
            )
            res1 = g.op("Mul", res1, alpha)
        if beta != 1:
            beta = g.op(
                "Constant",
                value_t=torch.tensor(
                    symbolic_helper._scalar(beta), dtype=scalar_type.dtype()
                ),
            )
            res2 = g.op("Mul", res2, beta)

        return g.op("Add", res1, res2)

    return g.op(
        "Gemm",
        mat1,
        mat2,
        self,
        beta_f=symbolic_helper._scalar(beta),
        alpha_f=symbolic_helper._scalar(alpha),
    )