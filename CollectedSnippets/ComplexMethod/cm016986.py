async def upload_images_to_comfyapi(
    cls: type[IO.ComfyNode],
    image: torch.Tensor | list[torch.Tensor],
    *,
    max_images: int = 8,
    mime_type: str | None = None,
    wait_label: str | None = "Uploading",
    show_batch_index: bool = True,
    total_pixels: int | None = 2048 * 2048,
) -> list[str]:
    """
    Uploads images to ComfyUI API and returns download URLs.
    To upload multiple images, stack them in the batch dimension first.
    """
    tensors: list[torch.Tensor] = []
    if isinstance(image, list):
        for img in image:
            is_batch = len(img.shape) > 3
            if is_batch:
                tensors.extend(img[i] for i in range(img.shape[0]))
            else:
                tensors.append(img)
    else:
        is_batch = len(image.shape) > 3
        if is_batch:
            tensors.extend(image[i] for i in range(image.shape[0]))
        else:
            tensors.append(image)

    # if batched, try to upload each file if max_images is greater than 0
    download_urls: list[str] = []
    num_to_upload = min(len(tensors), max_images)
    batch_start_ts = time.monotonic()

    for idx in range(num_to_upload):
        tensor = tensors[idx]
        img_io = tensor_to_bytesio(tensor, total_pixels=total_pixels, mime_type=mime_type)

        effective_label = wait_label
        if wait_label and show_batch_index and num_to_upload > 1:
            effective_label = f"{wait_label} ({idx + 1}/{num_to_upload})"

        url = await upload_file_to_comfyapi(cls, img_io, img_io.name, mime_type, effective_label, batch_start_ts)
        download_urls.append(url)
    return download_urls