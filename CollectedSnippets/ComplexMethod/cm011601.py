def tensor_split(
    a: TensorLikeType,
    indices_or_sections: Tensor | DimsType,
    dim: int = 0,
) -> tuple[TensorLikeType, ...]:
    _dim = utils.canonicalize_dim(a.ndim, dim)
    if a.ndim == 0:
        msg = "tensor_split: received a rank zero tensor, but expected a tensor of rank one or greater!"
        raise ValueError(msg)

    # If indices_or_sections is a tensor, it must be a CPU Long tensor
    if isinstance(indices_or_sections, TensorLike):
        if indices_or_sections.device.type != "cpu":
            msg = (
                f"tensor_split: if indices_or_sections is a tensor it must be on the CPU, "
                f"but received one on {indices_or_sections.device}"
            )
            raise ValueError(msg)
        if indices_or_sections.dtype != torch.long:
            msg = (
                "tensor_split: if indices_or_sections is a tensor it must have long dtype, "
                f" but received one with dtype {indices_or_sections.dtype}"
            )
            raise ValueError(msg)

    # Case 0 -- indices_or_sections is an integer or a scalar tensor n and a is split along dim into n parts of equal-ish length
    if isinstance(indices_or_sections, IntLike) or (
        isinstance(indices_or_sections, TensorLike) and indices_or_sections.ndim == 0
    ):
        sections: int = (
            indices_or_sections  # type: ignore[assignment]
            if isinstance(indices_or_sections, Number)
            else indices_or_sections.item()
        )

        if sections <= 0:
            msg = f"tensor_split: number of sections must be greater than 0, but was {sections}"
            raise ValueError(msg)

        dim_size = a.shape[_dim]
        min_split_size = math.floor(dim_size / sections)
        num_splits_one_extra = dim_size % sections

        split_sizes = []
        for split_idx in range(sections):
            split_size = (
                min_split_size + 1
                if (split_idx < num_splits_one_extra)
                else min_split_size
            )
            split_sizes.append(split_size)

        return tuple(aten.split_with_sizes(a, split_sizes, dim=_dim))
    # Case 1 -- indices_or_sections is a sequence of integers or a 1D tensor describing the splits
    else:
        indices = indices_or_sections
        if isinstance(indices_or_sections, TensorLike):
            if indices_or_sections.ndim != 1:
                msg = (
                    "tensor_split: non-scalar indices_or_sections tensors must have only one dimension, "
                    f"but received a tensor with {indices_or_sections.ndim} dimensions"
                )
                raise ValueError(msg)

            indices = indices_or_sections.tolist()

        indices = [0] + list(indices) + [a.shape[_dim]]
        split_sizes = [indices[i + 1] - indices[i] for i in range(len(indices) - 1)]
        return tuple(aten.split_with_sizes(a, split_sizes, dim=_dim))