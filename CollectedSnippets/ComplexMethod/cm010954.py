def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 1e-3,
        betas: tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        maximize: bool = False,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if not 0.0 < lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 < eps:
            raise ValueError(f"Invalid epsilon value: {eps}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 0: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta parameter at index 1: {betas[1]}")

        defaults = {
            "lr": lr,
            "betas": betas,
            "eps": eps,
            "maximize": maximize,
        }
        super().__init__(params, defaults)

        sparse_params = []
        complex_params = []
        for index, param_group in enumerate(self.param_groups):
            if not isinstance(param_group, dict):
                raise AssertionError(
                    f"param_groups must be a list of dicts, but got {type(param_group)}"
                )
            # given param group, convert given params to a list first before iterating
            for d_index, d_param in enumerate(param_group["params"]):
                if d_param.is_sparse:
                    sparse_params.append([index, d_index])
                if d_param.is_complex():
                    complex_params.append([index, d_index])
        if sparse_params:
            raise ValueError(
                f"Sparse params at indices {sparse_params}: SparseAdam requires dense parameter tensors"
            )
        if complex_params:
            raise ValueError(
                f"Complex params at indices {complex_params}: SparseAdam does not support complex parameters"
            )