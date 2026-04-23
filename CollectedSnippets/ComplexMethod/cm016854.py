def _prepare_latents_and_count(latents, dtype, bucket_mode):
    """Convert latents to dtype and compute image counts.

    Args:
        latents: Latents (tensor, list of tensors, or bucket list)
        dtype: Target dtype
        bucket_mode: Whether bucket mode is enabled

    Returns:
        tuple: (processed_latents, num_images, multi_res)
    """
    if bucket_mode:
        # In bucket mode, latents is list of tensors (Bi, C, Hi, Wi)
        latents = [t.to(dtype) for t in latents]
        num_buckets = len(latents)
        num_images = sum(t.shape[0] for t in latents)
        multi_res = False  # Not using multi_res path in bucket mode

        logging.debug(f"Bucket mode: {num_buckets} buckets, {num_images} total samples")
        for i, lat in enumerate(latents):
            logging.debug(f"  Bucket {i}: shape {lat.shape}")
        return latents, num_images, multi_res

    # Non-bucket mode
    if isinstance(latents, list):
        all_shapes = set()
        latents = [t.to(dtype) for t in latents]
        for latent in latents:
            all_shapes.add(latent.shape)
        logging.debug(f"Latent shapes: {all_shapes}")
        if len(all_shapes) > 1:
            multi_res = True
        else:
            multi_res = False
            latents = torch.cat(latents, dim=0)
        num_images = len(latents)
    elif isinstance(latents, torch.Tensor):
        latents = latents.to(dtype)
        num_images = latents.shape[0]
        multi_res = False
    else:
        logging.error(f"Invalid latents type: {type(latents)}")
        num_images = 0
        multi_res = False

    return latents, num_images, multi_res