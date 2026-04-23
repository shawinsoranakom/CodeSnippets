async def execute(
        cls,
        image: Input.Image,
        prompt: str,
        scale_factor: str,
        optimized_for: str,
        creativity: int,
        hdr: int,
        resemblance: int,
        fractality: int,
        engine: str,
        auto_downscale: bool,
    ) -> IO.NodeOutput:
        if get_number_of_images(image) != 1:
            raise ValueError("Exactly one input image is required.")
        validate_image_aspect_ratio(image, (1, 3), (3, 1), strict=False)
        validate_image_dimensions(image, min_height=160, min_width=160)

        max_output_pixels = 25_300_000
        height, width = get_image_dimensions(image)
        requested_scale = int(scale_factor.rstrip("x"))
        output_pixels = height * width * requested_scale * requested_scale

        if output_pixels > max_output_pixels:
            if auto_downscale:
                # Find optimal scale factor that doesn't require >2x downscale.
                # Server upscales in 2x steps, so aggressive downscaling degrades quality.
                input_pixels = width * height
                scale = 2
                max_input_pixels = max_output_pixels // 4
                for candidate in [16, 8, 4, 2]:
                    if candidate > requested_scale:
                        continue
                    scale_output_pixels = input_pixels * candidate * candidate
                    if scale_output_pixels <= max_output_pixels:
                        scale = candidate
                        max_input_pixels = None
                        break
                    downscale_ratio = math.sqrt(scale_output_pixels / max_output_pixels)
                    if downscale_ratio <= 2.0:
                        scale = candidate
                        max_input_pixels = max_output_pixels // (candidate * candidate)
                        break

                if max_input_pixels is not None:
                    image = downscale_image_tensor(image, total_pixels=max_input_pixels)
                scale_factor = f"{scale}x"
            else:
                raise ValueError(
                    f"Output size ({width * requested_scale}x{height * requested_scale} = {output_pixels:,} pixels) "
                    f"exceeds maximum allowed size of {max_output_pixels:,} pixels. "
                    f"Use a smaller input image or lower scale factor."
                )

        final_height, final_width = get_image_dimensions(image)
        actual_scale = int(scale_factor.rstrip("x"))
        price_usd = _calculate_magnific_upscale_price_usd(final_width, final_height, actual_scale)

        initial_res = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/freepik/v1/ai/image-upscaler", method="POST"),
            response_model=TaskResponse,
            data=ImageUpscalerCreativeRequest(
                image=(await upload_images_to_comfyapi(cls, image, max_images=1, total_pixels=None))[0],
                scale_factor=scale_factor,
                optimized_for=optimized_for,
                creativity=creativity,
                hdr=hdr,
                resemblance=resemblance,
                fractality=fractality,
                engine=engine,
                prompt=prompt if prompt else None,
            ),
        )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/freepik/v1/ai/image-upscaler/{initial_res.task_id}"),
            response_model=TaskResponse,
            status_extractor=lambda x: x.status,
            price_extractor=lambda _: price_usd,
            poll_interval=10.0,
            max_poll_attempts=480,
        )
        return IO.NodeOutput(await download_url_to_image_tensor(final_response.generated[0]))