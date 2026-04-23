def linalg_matrix_norm(
    g: jit_utils.GraphContext,
    self: torch._C.Value,
    ord: torch._C.Value,
    dim: list[int],
    keepdim: bool,
    dtype: torch._C.Value,
):
    # Conditions based on https://pytorch.org/docs/stable/generated/torch.linalg.matrix_norm.html
    ord_value = symbolic_helper._parse_arg(ord, "s")
    if ord_value == "fro":
        return frobenius_norm(g, self, dim, keepdim)
    elif ord_value == "nuc":
        return symbolic_helper._unimplemented("linalg.matrix_norm", "ord==nuc", self)
    else:
        ord_value = symbolic_helper._parse_arg(ord, "f")
        if ord_value is None:
            return frobenius_norm(g, self, dim, keepdim)
        if ord_value == 2 or ord_value == -2:
            # ord = 2/-2 unimplemented due to lack of operators
            # used to calculate singular values
            return symbolic_helper._unimplemented("linalg.matrix_norm", "ord==2", self)
        # Wrap the dim vector to handle negative dim values
        self_dim = symbolic_helper._get_tensor_rank(self)
        if self_dim is None:
            return symbolic_helper._unimplemented(
                "linalg.matrix_norm", "Input rank must be known at export time.", self
            )
        # Common implementation for cases with
        # ord = 1/-1 and ord = inf/-inf
        if dim[0] < 0:
            dim[0] += self_dim
        if dim[1] < 0:
            dim[1] += self_dim

        if ord_value == math.inf or ord_value == -math.inf:
            dim[0], dim[1] = dim[1], dim[0]
        if dim[1] > dim[0] and not keepdim:
            dim[1] -= 1
        sum = symbolic_helper._reducesum_helper(
            g, g.op("Abs", self), axes_i=[dim[0]], keepdims_i=keepdim
        )
        if ord_value > 0:
            # pyrefly: ignore [no-matching-overload]
            result, _indices = max(
                g,
                sum,
                dim_or_y=g.op("Constant", value_t=torch.LongTensor([dim[1]])),
                keepdim=keepdim,
            )
        else:
            # pyrefly: ignore [no-matching-overload]
            result, _indices = min(
                g,
                sum,
                dim_or_y=g.op("Constant", value_t=torch.LongTensor([dim[1]])),
                keepdim=keepdim,
            )
        return result