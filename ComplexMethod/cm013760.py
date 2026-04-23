def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        max_norm: float | None = None,
        norm_type: float = 2.0,
        scale_grad_by_freq: bool = False,
        mode: str = "mean",
        sparse: bool = False,
        _weight: Tensor | None = None,
        include_last_offset: bool = False,
        padding_idx: int | None = None,
        device=None,
        dtype=None,
    ) -> None:
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.max_norm = max_norm
        self.norm_type = norm_type
        self.scale_grad_by_freq = scale_grad_by_freq
        if padding_idx is not None:
            if padding_idx > 0:
                if padding_idx >= self.num_embeddings:
                    raise AssertionError("padding_idx must be within num_embeddings")
            elif padding_idx < 0:
                if padding_idx < -self.num_embeddings:
                    raise AssertionError("padding_idx must be within num_embeddings")
                padding_idx = self.num_embeddings + padding_idx
        self.padding_idx = padding_idx
        if _weight is None:
            self.weight = Parameter(
                torch.empty((num_embeddings, embedding_dim), **factory_kwargs)
            )
            self.reset_parameters()
        else:
            if list(_weight.shape) != [num_embeddings, embedding_dim]:
                raise AssertionError(
                    "Shape of weight does not match num_embeddings and embedding_dim"
                )
            self.weight = Parameter(_weight)
        self.mode = mode
        self.sparse = sparse
        self.include_last_offset = include_last_offset