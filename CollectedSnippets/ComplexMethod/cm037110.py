def get_image_size_for_max_num_patches(
    image_height: int,
    image_width: int,
    patch_size: int,
    max_num_patches: int,
    min_num_patches: int | None = None,
    eps: float = 1e-5,
    pixel_shuffle_scale: int = 1,
) -> tuple[int, int]:
    r"""Compute a target resolution whose patch grid satisfies patching parametrization.

    Args:
        image_height (`int`):
            Height in pixels of the source image prior to any resizing.
        image_width (`int`):
            Width in pixels of the source image prior to any resizing.
        patch_size (`int`):
            Size of the square patch used by the vision encoder.
        max_num_patches (`int`):
            Upper bound on `(height / patch_size) * (width / patch_size)` after
            resizing.
        min_num_patches (`int`, *optional*):
            Lower bound on the number of patches. When provided the image will
            be scaled up if necessary.
        eps (`float`, *optional*, defaults to 1e-5):
            Convergence tolerance for the internal binary search to determine
            the target dimensions.
        pixel_shuffle_scale (`int`, *optional*, defaults to 1):
            Additional stride multiplier applied when pixel shuffle later
            reduces spatial resolution.

    Returns:
        `tuple[int, int]`: Height and width (in pixels) that are multiples of
        `patch_size * pixel_shuffle_scale` and respect both the maximum and
        optional minimum patch-count constraints.
    """

    def get_scaled_image_size(scale, original_size, patch_size, pixel_shuffle_scale):
        scaled_size = scale * original_size
        divisor = patch_size * pixel_shuffle_scale
        scaled_size = math.ceil(scaled_size / divisor) * divisor
        scaled_size = max(divisor, scaled_size)
        return int(scaled_size)

    # Ensure divisibility
    divisor = patch_size * pixel_shuffle_scale
    adjusted_height = math.ceil(image_height / divisor) * divisor
    adjusted_height = max(divisor, adjusted_height)
    adjusted_width = math.ceil(image_width / divisor) * divisor
    adjusted_width = max(divisor, adjusted_width)

    num_patches = (adjusted_height / patch_size) * (adjusted_width / patch_size)

    if min_num_patches is not None and num_patches < min_num_patches:
        # Scale up
        scale_min, scale_max = 1.0, 100.0
        while (scale_max - scale_min) >= eps:
            scale = (scale_min + scale_max) / 2
            target_height = get_scaled_image_size(
                scale, image_height, patch_size, pixel_shuffle_scale
            )
            target_width = get_scaled_image_size(
                scale, image_width, patch_size, pixel_shuffle_scale
            )
            num_patches = (target_height / patch_size) * (target_width / patch_size)
            if num_patches >= min_num_patches:
                scale_max = scale
            else:
                scale_min = scale
        scale = scale_max
        target_height = get_scaled_image_size(
            scale, image_height, patch_size, pixel_shuffle_scale
        )
        target_width = get_scaled_image_size(
            scale, image_width, patch_size, pixel_shuffle_scale
        )
        return target_height, target_width
    elif num_patches <= max_num_patches:
        return adjusted_height, adjusted_width
    else:
        # Scale down
        scale_min, scale_max = eps / 10, 1.0
        while (scale_max - scale_min) >= eps:
            scale = (scale_min + scale_max) / 2
            target_height = get_scaled_image_size(
                scale, image_height, patch_size, pixel_shuffle_scale
            )
            target_width = get_scaled_image_size(
                scale, image_width, patch_size, pixel_shuffle_scale
            )
            num_patches = (target_height / patch_size) * (target_width / patch_size)
            if num_patches <= max_num_patches:
                scale_min = scale
            else:
                scale_max = scale
        scale = scale_min
        target_height = get_scaled_image_size(
            scale, image_height, patch_size, pixel_shuffle_scale
        )
        target_width = get_scaled_image_size(
            scale, image_width, patch_size, pixel_shuffle_scale
        )
        return target_height, target_width