def inplace_constant_pad_nd(
    x: TensorBox, padding: Sequence[int], fill_value: float
) -> TensorBox | None:
    """
    This optimization changes the semantics of padding from 'clone'
    style to 'view' style.

    Thanks to functionalization, this change can still maintain numerical
    correctness.
    """

    def _padding_can_be_fused():
        """
        Conservatively check if padding can be fused with downstream op.
        1. if the downstream op is a sum, then there is little benefit to
           do inplace padding
        2. if the downstream op is a matmul, doing inplace padding can
           save membw.
        """
        current_node = V.graph.current_node
        if current_node is None:
            return True  # be conservative
        users = tuple(current_node.users)
        if len(users) == 1 and users[0].target in (
            aten.mm.default,
            aten.addmm.default,
        ):
            return False

        return True  # be conservative

    if _padding_can_be_fused():
        return None

    # Only handle 2D case for now
    if len(padding) != 4 or len(x.get_size()) != 2:
        return None

    # No harm to realize since we already know that
    # the op can not be fused into the single user.
    # It need to be realized later anyways.
    x.realize()

    # If x is a view (e.g. a SliceView), realizing it just realizing the
    # underlying storage. x itself is still a view.
    if (
        not isinstance(x, ir.TensorBox)
        or not isinstance(x.data, ir.StorageBox)
        or not (
            isinstance(x.data.data, ir.ComputedBuffer)
            or (
                config.can_inplace_pad_graph_input
                and isinstance(x.data.data, ir.InputBuffer)
            )
        )
        or not x.data.data.name
    ):
        return None
    x.freeze_layout()

    _, layout = ir.as_storage_and_layout(x)
    strides = layout.stride
    if strides[1] != 1:
        return None

    if padding[0] != 0 or padding[2] != 0 or padding[3] != 0:
        return None

    npad = padding[1]
    if npad == 0:
        return None

    stride0 = strides[0]
    rowsize = layout.size[1]

    if stride0 < rowsize + npad:
        return None

    bufname = x.data.data.name
    padded_size = [layout.size[0], layout.size[1] + npad]
    V.graph.buffer_to_padded_size[bufname] = padded_size
    resized_x = as_strided(
        x,
        padded_size,
        layout.stride,
        layout.offset,
    )

    sliced_x = slice_(resized_x, dim=1, start=rowsize, end=rowsize + npad, clamp=False)
    fill_(sliced_x, fill_value)

    counters["inductor"]["inplace_padding"] += 1
    return resized_x