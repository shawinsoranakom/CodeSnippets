def apply_adaptive_masks(
        settings: SoftInpaintingSettings,
        nmask,
        latent_orig,
        latent_processed,
        overlay_images,
        width, height,
        paste_to):
    import torch
    import modules.processing as proc
    import modules.images as images
    from PIL import Image, ImageOps, ImageFilter

    # TODO: Bias the blending according to the latent mask, add adjustable parameter for bias control.
    if len(nmask.shape) == 3:
        latent_mask = nmask[0].float()
    else:
        latent_mask = nmask[:, 0].float()
    # convert the original mask into a form we use to scale distances for thresholding
    mask_scalar = 1 - (torch.clamp(latent_mask, min=0, max=1) ** (settings.mask_blend_scale / 2))
    mask_scalar = (0.5 * (1 - settings.composite_mask_influence)
                   + mask_scalar * settings.composite_mask_influence)
    mask_scalar = mask_scalar / (1.00001 - mask_scalar)
    mask_scalar = mask_scalar.cpu().numpy()

    latent_distance = torch.norm(latent_processed - latent_orig, p=2, dim=1)

    kernel, kernel_center = get_gaussian_kernel(stddev_radius=1.5, max_radius=2)

    masks_for_overlay = []

    for i, (distance_map, overlay_image) in enumerate(zip(latent_distance, overlay_images)):
        converted_mask = distance_map.float().cpu().numpy()
        converted_mask = weighted_histogram_filter(converted_mask, kernel, kernel_center,
                                                   percentile_min=0.9, percentile_max=1, min_width=1)
        converted_mask = weighted_histogram_filter(converted_mask, kernel, kernel_center,
                                                   percentile_min=0.25, percentile_max=0.75, min_width=1)

        # The distance at which opacity of original decreases to 50%
        if len(mask_scalar.shape) == 3:
            if mask_scalar.shape[0] > i:
                half_weighted_distance = settings.composite_difference_threshold * mask_scalar[i]
            else:
                half_weighted_distance = settings.composite_difference_threshold * mask_scalar[0]
        else:
            half_weighted_distance = settings.composite_difference_threshold * mask_scalar

        converted_mask = converted_mask / half_weighted_distance

        converted_mask = 1 / (1 + converted_mask ** settings.composite_difference_contrast)
        converted_mask = smootherstep(converted_mask)
        converted_mask = 1 - converted_mask
        converted_mask = 255. * converted_mask
        converted_mask = converted_mask.astype(np.uint8)
        converted_mask = Image.fromarray(converted_mask)
        converted_mask = images.resize_image(2, converted_mask, width, height)
        converted_mask = proc.create_binary_mask(converted_mask, round=False)

        # Remove aliasing artifacts using a gaussian blur.
        converted_mask = converted_mask.filter(ImageFilter.GaussianBlur(radius=4))

        # Expand the mask to fit the whole image if needed.
        if paste_to is not None:
            converted_mask = proc.uncrop(converted_mask,
                                         (overlay_image.width, overlay_image.height),
                                         paste_to)

        masks_for_overlay.append(converted_mask)

        image_masked = Image.new('RGBa', (overlay_image.width, overlay_image.height))
        image_masked.paste(overlay_image.convert("RGBA").convert("RGBa"),
                           mask=ImageOps.invert(converted_mask.convert('L')))

        overlay_images[i] = image_masked.convert('RGBA')

    return masks_for_overlay
