def load_image_as_tensor(
    image: Union[str, "PIL.Image.Image"],
    timeout: float | None = None,
) -> "torch.Tensor":
    """
    Loads `image` directly to a `torch.Tensor` using torchvision.

    Args:
        image (`str` or `PIL.Image.Image`):
            The image to convert to the PIL Image format.
        timeout (`float`, *optional*):
            The timeout value in seconds for the URL request.

    Returns:
        `torch.Tensor`: A `[C, H, W]` uint8 tensor in RGB channel order.
    """
    import torch

    if isinstance(image, str):
        if image.startswith("http://") or image.startswith("https://"):
            raw = httpx.get(image, timeout=timeout, follow_redirects=True).content
            buf = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
            return decode_image(buf, mode=ImageReadMode.RGB)
        elif os.path.isfile(image):
            return decode_image(image, mode=ImageReadMode.RGB)
        else:
            if image.startswith("data:image/"):
                image = image.split(",")[1]
            try:
                raw = base64.decodebytes(image.encode())
            except Exception as e:
                raise ValueError(
                    f"Incorrect image source. Must be a valid URL starting with `http://` or `https://`, a valid path to an image file, or a base64 encoded string. Got {image}. Failed with {e}"
                )
            buf = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
            return decode_image(buf, mode=ImageReadMode.RGB)
    elif isinstance(image, PIL.Image.Image):
        image = PIL.ImageOps.exif_transpose(image)
        return pil_to_tensor(image.convert("RGB"))
    else:
        raise TypeError(
            "Incorrect format used for image. Should be a URL, a local path, a base64 string, or a PIL image."
        )