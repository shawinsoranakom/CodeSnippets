def scale_to_multiple_cover(input: torch.Tensor, multiple: int, scale_method: str) -> torch.Tensor:
    if multiple <= 1:
        return input
    is_type_image = is_image(input)
    if is_type_image:
        _, height, width, _ = input.shape
    else:
        _, height, width = input.shape
    target_w = (width // multiple) * multiple
    target_h = (height // multiple) * multiple
    if target_w == 0 or target_h == 0:
        return input
    if target_w == width and target_h == height:
        return input
    s_w = target_w / width
    s_h = target_h / height
    if s_w >= s_h:
        scaled_w = target_w
        scaled_h = int(math.ceil(height * s_w))
        if scaled_h < target_h:
            scaled_h = target_h
    else:
        scaled_h = target_h
        scaled_w = int(math.ceil(width * s_h))
        if scaled_w < target_w:
            scaled_w = target_w
    input = init_image_mask_input(input, is_type_image)
    input = comfy.utils.common_upscale(input, scaled_w, scaled_h, scale_method, "disabled")
    input = finalize_image_mask_input(input, is_type_image)
    x0 = (scaled_w - target_w) // 2
    y0 = (scaled_h - target_h) // 2
    x1 = x0 + target_w
    y1 = y0 + target_h
    if is_type_image:
        return input[:, y0:y1, x0:x1, :]
    return input[:, y0:y1, x0:x1]