def _image_may_have_alpha_channel(image: PILImage) -> bool:
    if image.mode in ("RGBA", "LA", "P"):
        return True
    else:
        return False