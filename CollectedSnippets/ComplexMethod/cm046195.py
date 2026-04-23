def get_abs_pos(
    abs_pos: torch.Tensor,
    has_cls_token: bool,
    hw: tuple[int, int],
    retain_cls_token: bool = False,
    tiling: bool = False,
) -> torch.Tensor:
    """Calculate absolute positional embeddings. If needed, resize embeddings and remove cls_token dimension for the
    original embeddings.

    Args:
        abs_pos (torch.Tensor): Absolute positional embeddings with shape (1, num_position, C).
        has_cls_token (bool): If true, has 1 embedding in abs_pos for cls token.
        hw (tuple[int, int]): Size of input image tokens.
        retain_cls_token (bool): Whether to retain the cls_token.
        tiling (bool): Whether to tile the embeddings, *instead* of interpolation (a la abs_win).

    Returns:
        (torch.Tensor): Absolute positional embeddings after processing with shape (1, H, W, C) if retain_cls_token is
            False, otherwise (1, 1+H*W, C).
    """
    if retain_cls_token:
        assert has_cls_token

    h, w = hw
    if has_cls_token:
        cls_pos = abs_pos[:, :1]
        abs_pos = abs_pos[:, 1:]

    xy_num = abs_pos.shape[1]
    size = int(math.sqrt(xy_num))
    assert size * size == xy_num

    if size != h or size != w:
        new_abs_pos = abs_pos.reshape(1, size, size, -1).permute(0, 3, 1, 2)
        if tiling:
            new_abs_pos = new_abs_pos.tile([1, 1] + [x // y + 1 for x, y in zip((h, w), new_abs_pos.shape[2:])])[
                :, :, :h, :w
            ]
        else:
            new_abs_pos = F.interpolate(
                new_abs_pos,
                size=(h, w),
                mode="bicubic",
                align_corners=False,
            )

        if not retain_cls_token:
            return new_abs_pos.permute(0, 2, 3, 1)
        else:
            # add cls_token back, flatten spatial dims
            assert has_cls_token
            return torch.cat(
                [cls_pos, new_abs_pos.permute(0, 2, 3, 1).reshape(1, h * w, -1)],
                dim=1,
            )

    else:
        if not retain_cls_token:
            return abs_pos.reshape(1, h, w, -1)
        else:
            assert has_cls_token
            return torch.cat([cls_pos, abs_pos], dim=1)