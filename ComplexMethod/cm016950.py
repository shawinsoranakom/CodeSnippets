async def execute(
        cls,
        image: Input.Image,
        scale_factor: str,
        flavor: str,
        sharpen: int,
        smart_grain: int,
        ultra_detail: int,
        auto_downscale: bool,
    ) -> IO.NodeOutput:
        if get_number_of_images(image) != 1:
            raise ValueError("Exactly one input image is required.")
        validate_image_aspect_ratio(image, (1, 3), (3, 1), strict=False)
        validate_image_dimensions(image, min_height=160, min_width=160)

        max_output_dimension = 10060
        height, width = get_image_dimensions(image)
        requested_scale = int(scale_factor.strip("x"))
        output_width = width * requested_scale
        output_height = height * requested_scale

        if output_width > max_output_dimension or output_height > max_output_dimension:
            if auto_downscale:
                # Find optimal scale factor that doesn't require >2x downscale.
                # Server upscales in 2x steps, so aggressive downscaling degrades quality.
                max_dim = max(width, height)
                scale = 2
                max_input_dim = max_output_dimension // 2
                scale_ratio = max_input_dim / max_dim
                max_input_pixels = int(width * height * scale_ratio * scale_ratio)
                for candidate in [16, 8, 4, 2]:
                    if candidate > requested_scale:
                        continue
                    output_dim = max_dim * candidate
                    if output_dim <= max_output_dimension:
                        scale = candidate
                        max_input_pixels = None
                        break
                    downscale_ratio = output_dim / max_output_dimension
                    if downscale_ratio <= 2.0:
                        scale = candidate
                        max_input_dim = max_output_dimension // candidate
                        scale_ratio = max_input_dim / max_dim
                        max_input_pixels = int(width * height * scale_ratio * scale_ratio)
                        break

                if max_input_pixels is not None:
                    image = downscale_image_tensor(image, total_pixels=max_input_pixels)
                requested_scale = scale
            else:
                raise ValueError(
                    f"Output dimensions ({output_width}x{output_height}) exceed maximum allowed "
                    f"resolution of {max_output_dimension}x{max_output_dimension} pixels. "
                    f"Use a smaller input image or lower scale factor."
                )

        final_height, final_width = get_image_dimensions(image)
        price_usd = _calculate_magnific_upscale_price_usd(final_width, final_height, requested_scale)

        initial_res = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/freepik/v1/ai/image-upscaler-precision-v2", method="POST"),
            response_model=TaskResponse,
            data=ImageUpscalerPrecisionV2Request(
                image=(await upload_images_to_comfyapi(cls, image, max_images=1, total_pixels=None))[0],
                scale_factor=requested_scale,
                flavor=flavor,
                sharpen=sharpen,
                smart_grain=smart_grain,
                ultra_detail=ultra_detail,
            ),
        )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/freepik/v1/ai/image-upscaler-precision-v2/{initial_res.task_id}"),
            response_model=TaskResponse,
            status_extractor=lambda x: x.status,
            price_extractor=lambda _: price_usd,
            poll_interval=10.0,
            max_poll_attempts=480,
        )
        return IO.NodeOutput(await download_url_to_image_tensor(final_response.generated[0]))