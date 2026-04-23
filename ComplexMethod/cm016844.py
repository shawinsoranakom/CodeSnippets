def porter_duff_composite(src_image: torch.Tensor, src_alpha: torch.Tensor, dst_image: torch.Tensor, dst_alpha: torch.Tensor, mode: PorterDuffMode):
    # convert mask to alpha
    src_alpha = 1 - src_alpha
    dst_alpha = 1 - dst_alpha
    # premultiply alpha
    src_image = src_image * src_alpha
    dst_image = dst_image * dst_alpha

    # composite ops below assume alpha-premultiplied images
    if mode == PorterDuffMode.ADD:
        out_alpha = torch.clamp(src_alpha + dst_alpha, 0, 1)
        out_image = torch.clamp(src_image + dst_image, 0, 1)
    elif mode == PorterDuffMode.CLEAR:
        out_alpha = torch.zeros_like(dst_alpha)
        out_image = torch.zeros_like(dst_image)
    elif mode == PorterDuffMode.DARKEN:
        out_alpha = src_alpha + dst_alpha - src_alpha * dst_alpha
        out_image = (1 - dst_alpha) * src_image + (1 - src_alpha) * dst_image + torch.min(src_image, dst_image)
    elif mode == PorterDuffMode.DST:
        out_alpha = dst_alpha
        out_image = dst_image
    elif mode == PorterDuffMode.DST_ATOP:
        out_alpha = src_alpha
        out_image = src_alpha * dst_image + (1 - dst_alpha) * src_image
    elif mode == PorterDuffMode.DST_IN:
        out_alpha = src_alpha * dst_alpha
        out_image = dst_image * src_alpha
    elif mode == PorterDuffMode.DST_OUT:
        out_alpha = (1 - src_alpha) * dst_alpha
        out_image = (1 - src_alpha) * dst_image
    elif mode == PorterDuffMode.DST_OVER:
        out_alpha = dst_alpha + (1 - dst_alpha) * src_alpha
        out_image = dst_image + (1 - dst_alpha) * src_image
    elif mode == PorterDuffMode.LIGHTEN:
        out_alpha = src_alpha + dst_alpha - src_alpha * dst_alpha
        out_image = (1 - dst_alpha) * src_image + (1 - src_alpha) * dst_image + torch.max(src_image, dst_image)
    elif mode == PorterDuffMode.MULTIPLY:
        out_alpha = src_alpha * dst_alpha
        out_image = src_image * dst_image
    elif mode == PorterDuffMode.OVERLAY:
        out_alpha = src_alpha + dst_alpha - src_alpha * dst_alpha
        out_image = torch.where(2 * dst_image < dst_alpha, 2 * src_image * dst_image,
            src_alpha * dst_alpha - 2 * (dst_alpha - src_image) * (src_alpha - dst_image))
    elif mode == PorterDuffMode.SCREEN:
        out_alpha = src_alpha + dst_alpha - src_alpha * dst_alpha
        out_image = src_image + dst_image - src_image * dst_image
    elif mode == PorterDuffMode.SRC:
        out_alpha = src_alpha
        out_image = src_image
    elif mode == PorterDuffMode.SRC_ATOP:
        out_alpha = dst_alpha
        out_image = dst_alpha * src_image + (1 - src_alpha) * dst_image
    elif mode == PorterDuffMode.SRC_IN:
        out_alpha = src_alpha * dst_alpha
        out_image = src_image * dst_alpha
    elif mode == PorterDuffMode.SRC_OUT:
        out_alpha = (1 - dst_alpha) * src_alpha
        out_image = (1 - dst_alpha) * src_image
    elif mode == PorterDuffMode.SRC_OVER:
        out_alpha = src_alpha + (1 - src_alpha) * dst_alpha
        out_image = src_image + (1 - src_alpha) * dst_image
    elif mode == PorterDuffMode.XOR:
        out_alpha = (1 - dst_alpha) * src_alpha + (1 - src_alpha) * dst_alpha
        out_image = (1 - dst_alpha) * src_image + (1 - src_alpha) * dst_image
    else:
        return None, None

    # back to non-premultiplied alpha
    out_image = torch.where(out_alpha > 1e-5, out_image / out_alpha, torch.zeros_like(out_image))
    out_image = torch.clamp(out_image, 0, 1)
    # convert alpha to mask
    out_alpha = 1 - out_alpha
    return out_image, out_alpha