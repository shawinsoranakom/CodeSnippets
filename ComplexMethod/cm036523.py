def _get_expected_num_patches(
    config: PretrainedConfig,
    image: Image.Image,
    num_imgs: int,
    min_num: int,
    max_num: int,
):
    from vllm.transformers_utils.processors.h2ovl import (
        calculate_h2ovl_targets,
        get_h2ovl_target_ratios,
    )

    width, height = image.size

    # Calculate the expected number of blocks
    if num_imgs == 1 and config.use_msac:
        # First pass
        blocks1, _, _, aspect_ratio = calculate_h2ovl_targets(
            orig_width=width,
            orig_height=height,
            target_ratios=get_h2ovl_target_ratios(
                min_num=1,
                max_num=max_num,
                prior_aspect_ratio=None,
            ),
            image_size=config.vision_config.image_size,
            use_thumbnail=False,  # Thumbnail is handled separately
        )

        # Second pass
        blocks2, _, _, _ = calculate_h2ovl_targets(
            orig_width=width,
            orig_height=height,
            target_ratios=get_h2ovl_target_ratios(
                min_num=3,
                max_num=max_num,
                prior_aspect_ratio=aspect_ratio,
            ),
            image_size=config.vision_config.image_size,
            use_thumbnail=False,
        )

        # Add thumbnail if use_thumbnail is True and total_blocks > 1
        if config.use_thumbnail:
            blocks1 += 1 if blocks1 > 1 else 0
            blocks2 += 1 if blocks2 > 1 else 0

        # Total blocks is the sum of blocks from both passes minus
        # overlapping
        total_blocks = blocks1 + blocks2 - 1

        return total_blocks

    blocks, _, _, _ = calculate_h2ovl_targets(
        orig_width=width,
        orig_height=height,
        target_ratios=get_h2ovl_target_ratios(
            min_num,
            max_num,
            prior_aspect_ratio=None,
        ),
        image_size=config.vision_config.image_size,
        use_thumbnail=False,
    )
    expected_num_patches = blocks

    if config.use_thumbnail and expected_num_patches > 1:
        expected_num_patches += 1

    return expected_num_patches