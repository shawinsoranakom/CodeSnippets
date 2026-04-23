async def execute(
        cls,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        duration: int,
        reference_video: Input.Video,
        keep_original_sound: bool,
        reference_images: Input.Image | None = None,
        resolution: str = "1080p",
        seed: int = 0,
    ) -> IO.NodeOutput:
        _ = seed
        prompt = normalize_omni_prompt_references(prompt)
        validate_string(prompt, min_length=1, max_length=2500)
        validate_video_duration(reference_video, min_duration=3.0, max_duration=10.05)
        validate_video_dimensions(reference_video, min_width=720, min_height=720, max_width=2160, max_height=2160)
        image_list: list[OmniParamImage] = []
        if reference_images is not None:
            if get_number_of_images(reference_images) > 4:
                raise ValueError("The maximum number of reference images allowed with a video input is 4.")
            for i in reference_images:
                validate_image_dimensions(i, min_width=300, min_height=300)
                validate_image_aspect_ratio(i, (1, 2.5), (2.5, 1))
            for i in await upload_images_to_comfyapi(cls, reference_images, wait_label="Uploading reference image"):
                image_list.append(OmniParamImage(image_url=i))
        video_list = [
            OmniParamVideo(
                video_url=await upload_video_to_comfyapi(cls, reference_video, wait_label="Uploading reference video"),
                refer_type="feature",
                keep_original_sound="yes" if keep_original_sound else "no",
            )
        ]
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/kling/v1/videos/omni-video", method="POST"),
            response_model=TaskStatusResponse,
            data=OmniProReferences2VideoRequest(
                model_name=model_name,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=str(duration),
                image_list=image_list if image_list else None,
                video_list=video_list,
                mode="pro" if resolution == "1080p" else "std",
            ),
        )
        return await finish_omni_video_task(cls, response)