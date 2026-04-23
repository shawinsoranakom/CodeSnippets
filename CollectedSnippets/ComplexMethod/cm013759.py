def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        padding_idx: int | None = None,
        max_norm: float | None = None,
        norm_type: float = 2.0,
        scale_grad_by_freq: bool = False,
        sparse: bool = False,
        _weight: Tensor | None = None,
        _freeze: bool = False,
        device=None,
        dtype=None,
    ) -> None:
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        if padding_idx is not None:
            if padding_idx > 0:
                if padding_idx >= self.num_embeddings:
                    raise AssertionError("Padding_idx must be within num_embeddings")
            elif padding_idx < 0:
                if padding_idx < -self.num_embeddings:
                    raise AssertionError("Padding_idx must be within num_embeddings")
                padding_idx = self.num_embeddings + padding_idx
        self.padding_idx = padding_idx
        self.max_norm = max_norm
        self.norm_type = norm_type
        self.scale_grad_by_freq = scale_grad_by_freq
        if _weight is None:
            self.weight = Parameter(
                torch.empty((num_embeddings, embedding_dim), **factory_kwargs),
                requires_grad=not _freeze,
            )
            self.reset_parameters()
        else:
            if list(_weight.shape) != [num_embeddings, embedding_dim]:
                raise AssertionError(
                    "Shape of weight does not match num_embeddings and embedding_dim"
                )
            self.weight = Parameter(_weight, requires_grad=not _freeze)

        self.sparse = sparse