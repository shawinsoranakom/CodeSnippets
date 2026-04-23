def tensor_split_tensor_indices_or_sections_py_impl(
    self: Tensor,
    tensor_indices_or_sections: Tensor,
    dim: int = 0,
) -> tuple[Tensor, ...]:
    if tensor_indices_or_sections.device.type != "cpu":
        raise AssertionError(
            f"tensor_indices_or_sections must be on CPU, got {tensor_indices_or_sections.device}"
        )
    if tensor_indices_or_sections.dtype != torch.int64:
        raise AssertionError(
            f"tensor_indices_or_sections must be int64, got {tensor_indices_or_sections.dtype}"
        )
    split_dim = tensor_indices_or_sections.dim()
    torch._check(
        split_dim == 1 or split_dim == 0,
        lambda: "tensor_split expected tensor_indices_or_sections to be a zero-dimensional "
        f"or one-dimensional tensor, but got a tensor with {split_dim} dims",
    )
    if split_dim == 0:
        sections = tensor_indices_or_sections.item()
        if not isinstance(sections, IntLike):
            raise AssertionError(
                f"Expected sections to be IntLike, got {type(sections).__name__}"
            )
        return self.tensor_split(sections, dim)
    else:
        ctx = nullcontext
        if (fake_mode := torch._guards.detect_fake_mode()) and (
            shape_env := fake_mode.shape_env
        ):
            ctx = shape_env.ignore_fresh_unbacked_symbols  # type: ignore[assignment]
        # In fake tensor prop, we end up calling slice() with these unbacked indices.
        # Because slice has flexible semantics, the unbacked handling generates new output sizes
        # for each slice, effectively clobbering over these index symbols.
        # To avoid PendingUnbackedSymbolNotFound errors, we tell the compiler it's fine to not bind these.
        with ctx():
            indices = [i.item() for i in tensor_indices_or_sections]
        # WARNING: Tempted to torch._check(x>0) on the indices here?  You
        # can't: tensor_split works with negative values in indices:
        #
        # >>> torch.tensor_split(torch.randn(10), torch.tensor([-5, 5]))
        # (tensor([ 0.3540,  2.1074, -0.8507,  1.1639,  0.3055]), tensor([]),
        # tensor([-0.4285,  1.0692, -0.1776,  0.9362,  1.6143]))
        #
        # Sorry, I don't make the rules.  Explicitly do the item call in user
        # code if you KNOW that they are non-negative.
        return self.tensor_split(indices, dim)