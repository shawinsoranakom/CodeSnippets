def tiled_upscale_2(
    img: torch.Tensor,
    model,
    *,
    tile_size: int,
    tile_overlap: int,
    scale: int,
    device: torch.device,
    desc="Tiled upscale",
):
    # Alternative implementation of `upscale_with_model` originally used by
    # SwinIR and ScuNET.  It differs from `upscale_with_model` in that tiling and
    # weighting is done in PyTorch space, as opposed to `images.Grid` doing it in
    # Pillow space without weighting.

    b, c, h, w = img.size()
    tile_size = min(tile_size, h, w)

    if tile_size <= 0:
        logger.debug("Upscaling %s without tiling", img.shape)
        return model(img)

    stride = tile_size - tile_overlap
    h_idx_list = list(range(0, h - tile_size, stride)) + [h - tile_size]
    w_idx_list = list(range(0, w - tile_size, stride)) + [w - tile_size]
    result = torch.zeros(
        b,
        c,
        h * scale,
        w * scale,
        device=device,
        dtype=img.dtype,
    )
    weights = torch.zeros_like(result)
    logger.debug("Upscaling %s to %s with tiles", img.shape, result.shape)
    with tqdm.tqdm(total=len(h_idx_list) * len(w_idx_list), desc=desc, disable=not shared.opts.enable_upscale_progressbar) as pbar:
        for h_idx in h_idx_list:
            if shared.state.interrupted or shared.state.skipped:
                break

            for w_idx in w_idx_list:
                if shared.state.interrupted or shared.state.skipped:
                    break

                # Only move this patch to the device if it's not already there.
                in_patch = img[
                    ...,
                    h_idx : h_idx + tile_size,
                    w_idx : w_idx + tile_size,
                ].to(device=device)

                out_patch = model(in_patch)

                result[
                    ...,
                    h_idx * scale : (h_idx + tile_size) * scale,
                    w_idx * scale : (w_idx + tile_size) * scale,
                ].add_(out_patch)

                out_patch_mask = torch.ones_like(out_patch)

                weights[
                    ...,
                    h_idx * scale : (h_idx + tile_size) * scale,
                    w_idx * scale : (w_idx + tile_size) * scale,
                ].add_(out_patch_mask)

                pbar.update(1)

    output = result.div_(weights)

    return output