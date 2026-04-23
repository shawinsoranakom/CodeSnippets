def linalg_norm(
    g: jit_utils.GraphContext,
    self: torch._C.Value,
    ord: torch._C.Value,
    dim: Sequence[int] | None,
    keepdim: bool,
    dtype: torch._C.Value,
):
    # Conditions based on https://pytorch.org/docs/stable/generated/torch.linalg.norm.html
    ord_value = None
    if dim is None:
        if symbolic_helper._is_none(ord):
            self = symbolic_helper._reshape_helper(g, self, [-1])
            ord = g.op("Constant", value_t=torch.LongTensor([2]))
        self_dim = symbolic_helper._get_tensor_rank(self)
        if self_dim is None:
            return symbolic_helper._unimplemented(
                "dim", "Input rank must be known at export time.", self
            )
        if self_dim == 1:
            ord_value = symbolic_helper._parse_arg(ord, "f")
        else:
            dim = [0, 1]
    else:
        if len(dim) == 1:
            if symbolic_helper._is_none(ord):
                ord = g.op("Constant", value_t=torch.LongTensor([2]))
            ord_value = symbolic_helper._parse_arg(ord, "f")
    if ord_value:
        return linalg_vector_norm(g, self, ord_value, dim, keepdim, dtype)
    return linalg_matrix_norm(g, self, ord, dim, keepdim, dtype)