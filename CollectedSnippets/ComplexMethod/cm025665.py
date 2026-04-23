async def _async_get_image(
    camera: Camera,
    timeout: int = 10,
    width: int | None = None,
    height: int | None = None,
) -> Image:
    """Fetch a snapshot image from a camera.

    If width and height are passed, an attempt to scale
    the image will be made on a best effort basis.
    Not all cameras can scale images or return jpegs
    that we can scale, however the majority of cases
    are handled.
    """
    with suppress(asyncio.CancelledError, TimeoutError):
        async with asyncio.timeout(timeout):
            image_bytes = (
                await _async_get_stream_image(
                    camera, width=width, height=height, wait_for_next_keyframe=False
                )
                if camera.use_stream_for_stills
                else await camera.async_camera_image(width=width, height=height)
            )
            if image_bytes:
                content_type = camera.content_type
                image = Image(content_type, image_bytes)
                if (
                    width is not None
                    and height is not None
                    and ("jpeg" in content_type or "jpg" in content_type)
                ):
                    assert width is not None
                    assert height is not None
                    return Image(
                        content_type, scale_jpeg_camera_image(image, width, height)
                    )

                return image

    raise HomeAssistantError("Unable to get image")