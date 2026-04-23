def exif_transpose(
    images: ImageInput | None,
) -> ImageInput | None:
    if images is None:
        return None
    if images is not None and isinstance(images, (list, tuple)):
        images = [
            exif_transpose(img) if isinstance(img, Image) else img for img in images
        ]
    elif images is not None and isinstance(images, Image):
        images = ImageOps.exif_transpose(images)
    return images