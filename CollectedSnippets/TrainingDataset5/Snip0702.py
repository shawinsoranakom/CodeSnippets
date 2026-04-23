def apply_masks(
        settings,
        nmask,
        overlay_images,
        width, height,
        paste_to):
    import torch
    import modules.processing as proc
    import modules.images as images
    from PIL import Image, ImageOps, ImageFilter

    converted_mask = nmask[0].float()
    converted_mask = torch.clamp(converted_mask, min=0, max=1).pow_(settings.mask_blend_scale / 2)
    converted_mask = 255. * converted_mask
    converted_mask = converted_mask.cpu().numpy().astype(np.uint8)
    converted_mask = Image.fromarray(converted_mask)
    converted_mask = images.resize_image(2, converted_mask, width, height)
    converted_mask = proc.create_binary_mask(converted_mask, round=False)

    # Remove aliasing artifacts using a gaussian blur.
    converted_mask = converted_mask.filter(ImageFilter.GaussianBlur(radius=4))

    # Expand the mask to fit the whole image if needed.
    if paste_to is not None:
        converted_mask = proc.uncrop(converted_mask,
                                     (width, height),
                                     paste_to)

    masks_for_overlay = []

    for i, overlay_image in enumerate(overlay_images):
        masks_for_overlay[i] = converted_mask

        image_masked = Image.new('RGBa', (overlay_image.width, overlay_image.height))
        image_masked.paste(overlay_image.convert("RGBA").convert("RGBa"),
                           mask=ImageOps.invert(converted_mask.convert('L')))

        overlay_images[i] = image_masked.convert('RGBA')

    return masks_for_overlay
