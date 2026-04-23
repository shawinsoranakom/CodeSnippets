def addr(
    self: TensorLikeType,
    vec1: TensorLikeType,
    vec2: TensorLikeType,
    *,
    beta: NumberType = 1,
    alpha: NumberType = 1,
) -> TensorLikeType:
    torch._check(
        vec1.ndim == 1,
        lambda: f"addr: Expected 1-D argument vec1, but got {vec1.ndim}-D",
    )
    torch._check(
        vec2.ndim == 1,
        lambda: f"addr: Expected 1-D argument vec2, but got {vec2.ndim}-D",
    )
    for arg, arg_name in ((alpha, "alpha"), (beta, "beta")):
        if isinstance(arg, bool):
            torch._check(
                utils.is_boolean_dtype(self.dtype)
                and utils.is_boolean_dtype(vec1.dtype)
                and utils.is_boolean_dtype(vec2.dtype),
                lambda: f"Boolean {arg_name} only supported for Boolean results.",
            )
    self = self.expand(vec1.shape[0], vec2.shape[0])
    if utils.is_boolean_dtype(self.dtype):
        # Integers are accepted for booleans
        torch._check(
            is_weakly_lesser_type(type(beta), int),
            lambda: f"expected bool/int beta but got {type(beta)}",
        )
        torch._check(
            is_weakly_lesser_type(type(alpha), int),
            lambda: f"expected bool/int alpha but got {type(alpha)}",
        )
        if not beta:
            return torch.outer(vec1, vec2) if alpha else torch.full_like(self, False)
        else:
            return torch.logical_or(
                self,
                torch.outer(vec1, vec2) if alpha else torch.full_like(self, False),
            )
    else:
        torch._check(
            is_weakly_lesser_type(type(beta), dtype_to_type(self.dtype)),
            lambda: f"cannot safely convert {type(beta)} to {self.dtype}",
        )
        torch._check(
            is_weakly_lesser_type(type(alpha), dtype_to_type(self.dtype)),
            lambda: f"cannot safely convert {type(alpha)} to {self.dtype}",
        )
        if beta == 0:
            # This means NaNs from self are dropped if beta is zero
            return alpha * torch.outer(vec1, vec2)
        else:
            return beta * self + alpha * torch.outer(vec1, vec2)