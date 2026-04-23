def _in_projection(
    q: Tensor,
    k: Tensor,
    v: Tensor,
    w_q: Tensor,
    w_k: Tensor,
    w_v: Tensor,
    b_q: Tensor | None = None,
    b_k: Tensor | None = None,
    b_v: Tensor | None = None,
) -> tuple[Tensor, Tensor, Tensor]:
    r"""Perform the in-projection step of the attention operation.

    This is simply a triple of linear projections,
    with shape constraints on the weights which
    ensure embedding dimension uniformity in the projected outputs.
    Output is a triple containing projection tensors for query, key and value.

    Args:
        q, k, v: query, key and value tensors to be projected.
        w_q, w_k, w_v: weights for q, k and v, respectively.
        b_q, b_k, b_v: optional biases for q, k and v, respectively.

    Shape:
        Inputs:
        - q: :math:`(Qdims..., Eq)` where Eq is the query embedding dimension and Qdims are any
            number of leading dimensions.
        - k: :math:`(Kdims..., Ek)` where Ek is the key embedding dimension and Kdims are any
            number of leading dimensions.
        - v: :math:`(Vdims..., Ev)` where Ev is the value embedding dimension and Vdims are any
            number of leading dimensions.
        - w_q: :math:`(Eq, Eq)`
        - w_k: :math:`(Eq, Ek)`
        - w_v: :math:`(Eq, Ev)`
        - b_q: :math:`(Eq)`
        - b_k: :math:`(Eq)`
        - b_v: :math:`(Eq)`

        Output: in output triple :math:`(q', k', v')`,
         - q': :math:`[Qdims..., Eq]`
         - k': :math:`[Kdims..., Eq]`
         - v': :math:`[Vdims..., Eq]`

    """
    Eq, Ek, Ev = q.size(-1), k.size(-1), v.size(-1)
    if w_q.shape != (Eq, Eq):
        raise AssertionError(
            f"expecting query weights shape of {(Eq, Eq)}, but got {w_q.shape}"
        )
    if w_k.shape != (Eq, Ek):
        raise AssertionError(
            f"expecting key weights shape of {(Eq, Ek)}, but got {w_k.shape}"
        )
    if w_v.shape != (Eq, Ev):
        raise AssertionError(
            f"expecting value weights shape of {(Eq, Ev)}, but got {w_v.shape}"
        )
    if b_q is not None and b_q.shape != (Eq,):
        raise AssertionError(
            f"expecting query bias shape of {(Eq,)}, but got {b_q.shape}"
        )
    if b_k is not None and b_k.shape != (Eq,):
        raise AssertionError(
            f"expecting key bias shape of {(Eq,)}, but got {b_k.shape}"
        )
    if b_v is not None and b_v.shape != (Eq,):
        raise AssertionError(
            f"expecting value bias shape of {(Eq,)}, but got {b_v.shape}"
        )
    return linear(q, w_q, b_q), linear(k, w_k, b_k), linear(v, w_v, b_v)