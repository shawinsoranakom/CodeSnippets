def prelu(g: jit_utils.GraphContext, self, weight):
    self_rank = symbolic_helper._get_tensor_rank(self)
    weight_sizes = symbolic_helper._get_tensor_sizes(weight)
    weight_rank = len(weight_sizes)
    if self_rank is not None:
        if self_rank > 2:
            # make weight unidirectional broadcastable
            weight = symbolic_helper._unsqueeze_helper(
                g, weight, list(range(1, self_rank - 1))
            )
        elif self_rank == 0 and weight_sizes == [1]:
            # self and weight are both scalar but weight has rank == 1, squeeze weight.
            weight = symbolic_helper._squeeze_helper(g, weight, [0])
            weight_rank = 0

    if self_rank is not None and weight_rank is not None:
        if self_rank < weight_rank:
            raise AssertionError(
                f"rank(x) should be >= rank(slope) but got {self_rank} < {weight_rank}"
            )
    return g.op("PRelu", self, weight)