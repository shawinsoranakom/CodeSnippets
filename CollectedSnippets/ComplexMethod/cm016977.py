async def execute(
        cls,
        model: str,
        image: Input.Image,
        upscale_factor: int,
        auto_downscale: bool,
    ) -> IO.NodeOutput:
        height, width = get_image_dimensions(image)
        requested_scale = upscale_factor
        output_pixels = height * width * requested_scale * requested_scale
        if output_pixels > MAX_PIXELS_GENERATIVE:
            if auto_downscale:
                input_pixels = width * height
                scale = 1
                max_input_pixels = MAX_PIXELS_GENERATIVE

                for candidate in [4, 2, 1]:
                    if candidate > requested_scale:
                        continue
                    scale_output_pixels = input_pixels * candidate * candidate
                    if scale_output_pixels <= MAX_PIXELS_GENERATIVE:
                        scale = candidate
                        max_input_pixels = None
                        break
                    # Check if we can downscale input by at most 2x to fit
                    downscale_ratio = math.sqrt(scale_output_pixels / MAX_PIXELS_GENERATIVE)
                    if downscale_ratio <= 2.0:
                        scale = candidate
                        max_input_pixels = MAX_PIXELS_GENERATIVE // (candidate * candidate)
                        break

                if max_input_pixels is not None:
                    image = downscale_image_tensor(image, total_pixels=max_input_pixels)
                upscale_factor = scale
            else:
                output_width = width * requested_scale
                output_height = height * requested_scale
                raise ValueError(
                    f"Output size ({output_width}x{output_height} = {output_pixels:,} pixels) "
                    f"exceeds maximum allowed size of {MAX_PIXELS_GENERATIVE:,} pixels ({MAX_MP_GENERATIVE}MP). "
                    f"Enable auto_downscale or use a smaller input image or a lower upscale factor."
                )

        initial_res = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/hitpaw/api/photo-enhancer", method="POST"),
            response_model=TaskCreateResponse,
            data=ImageEnhanceTaskCreateRequest(
                model_name=f"{model}_{upscale_factor}x",
                img_url=await upload_image_to_comfyapi(cls, image, total_pixels=None),
            ),
            wait_label="Creating task",
            final_label_on_success="Task created",
        )
        if initial_res.code != 200:
            raise ValueError(f"Task creation failed with code {initial_res.code}: {initial_res.message}")
        request_price = initial_res.data.consume_coins / 1000
        final_response = await poll_op(
            cls,
            ApiEndpoint(path="/proxy/hitpaw/api/task-status", method="POST"),
            data=TaskCreateDataResponse(job_id=initial_res.data.job_id),
            response_model=TaskStatusResponse,
            status_extractor=lambda x: x.data.status,
            price_extractor=lambda x: request_price,
            poll_interval=10.0,
            max_poll_attempts=480,
        )
        return IO.NodeOutput(await download_url_to_image_tensor(final_response.data.res_url))