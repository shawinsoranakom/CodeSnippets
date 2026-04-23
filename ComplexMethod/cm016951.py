async def execute(
        cls,
        image: Input.Image,
        prompt: str,
        light_transfer_strength: int,
        style: str,
        interpolate_from_original: bool,
        change_background: bool,
        preserve_details: bool,
        advanced_settings: InputAdvancedSettings,
        reference_image: Input.Image | None = None,
    ) -> IO.NodeOutput:
        if get_number_of_images(image) != 1:
            raise ValueError("Exactly one input image is required.")
        if reference_image is not None and get_number_of_images(reference_image) != 1:
            raise ValueError("Exactly one reference image is required.")
        validate_image_aspect_ratio(image, (1, 3), (3, 1), strict=False)
        validate_image_dimensions(image, min_height=160, min_width=160)
        if reference_image is not None:
            validate_image_aspect_ratio(reference_image, (1, 3), (3, 1), strict=False)
            validate_image_dimensions(reference_image, min_height=160, min_width=160)

        image_url = (await upload_images_to_comfyapi(cls, image, max_images=1))[0]
        reference_url = None
        if reference_image is not None:
            reference_url = (await upload_images_to_comfyapi(cls, reference_image, max_images=1))[0]

        adv_settings = None
        if advanced_settings["advanced_settings"] == "enabled":
            adv_settings = ImageRelightAdvancedSettingsRequest(
                whites=advanced_settings["whites"],
                blacks=advanced_settings["blacks"],
                brightness=advanced_settings["brightness"],
                contrast=advanced_settings["contrast"],
                saturation=advanced_settings["saturation"],
                engine=advanced_settings["engine"],
                transfer_light_a=advanced_settings["transfer_light_a"],
                transfer_light_b=advanced_settings["transfer_light_b"],
                fixed_generation=advanced_settings["fixed_generation"],
            )

        initial_res = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/freepik/v1/ai/image-relight", method="POST"),
            response_model=TaskResponse,
            data=ImageRelightRequest(
                image=image_url,
                prompt=prompt if prompt else None,
                transfer_light_from_reference_image=reference_url,
                light_transfer_strength=light_transfer_strength,
                interpolate_from_original=interpolate_from_original,
                change_background=change_background,
                style=style,
                preserve_details=preserve_details,
                advanced_settings=adv_settings,
            ),
        )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/freepik/v1/ai/image-relight/{initial_res.task_id}"),
            response_model=TaskResponse,
            status_extractor=lambda x: x.status,
            poll_interval=10.0,
            max_poll_attempts=480,
        )
        return IO.NodeOutput(await download_url_to_image_tensor(final_response.generated[0]))