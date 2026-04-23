def __init__(
        self,
        params: ParamsT,
        lr: float | Tensor = 1e-2,
        alpha: float = 0.99,
        eps: float = 1e-8,
        weight_decay: float = 0,
        momentum: float = 0,
        centered: bool = False,
        capturable: bool = False,
        foreach: bool | None = None,
        maximize: bool = False,
        differentiable: bool = False,
    ) -> None:
        if isinstance(lr, Tensor) and lr.numel() != 1:
            raise ValueError("Tensor lr must be 1-element")
        if not 0.0 <= lr:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= eps:
            raise ValueError(f"Invalid epsilon value: {eps}")
        if not 0.0 <= momentum:
            raise ValueError(f"Invalid momentum value: {momentum}")
        if not 0.0 <= weight_decay:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")
        if not 0.0 <= alpha:
            raise ValueError(f"Invalid alpha value: {alpha}")

        defaults = {
            "lr": lr,
            "momentum": momentum,
            "alpha": alpha,
            "eps": eps,
            "centered": centered,
            "weight_decay": weight_decay,
            "capturable": capturable,
            "foreach": foreach,
            "maximize": maximize,
            "differentiable": differentiable,
        }
        super().__init__(params, defaults)