def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 1e-2,
        beta2_decay: float = -0.8,
        eps: tuple[float | None, float] = (None, 1e-3),
        d: float = 1.0,
        weight_decay: float = 0.0,
        *,
        foreach: bool | None = None,
        maximize: bool = False,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if not 0.0 <= lr:
            raise ValueError(f"Learning rate should be >= 0 but is: {lr}")
        if not 0.0 >= beta2_decay:
            raise ValueError(f"beta2_decay should be <= 0 but is: {beta2_decay}")
        if eps[0] is not None and not 0.0 <= eps[0]:
            raise ValueError(f"epsilon1 should be >= 0 but is: {eps[0]}")
        if not 0.0 <= eps[1]:
            raise ValueError(f"epsilon2 should be >= 0 but is: {eps[1]}")
        if not 1.0 <= d:
            raise ValueError(f"Clipping threshold d should be >= 1 but is: {d}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"weight_decay should be >= 0 but is: {weight_decay}")
        defaults = {
            "lr": lr,
            "beta2_decay": beta2_decay,
            "eps": eps,
            "d": d,
            "weight_decay": weight_decay,
            "foreach": foreach,
            "maximize": maximize,
        }
        super().__init__(params, defaults)