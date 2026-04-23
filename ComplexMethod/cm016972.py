async def execute(
        cls,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        duration: int,
        reference_images: Input.Image,
        resolution: str = "1080p",
        storyboards: dict | None = None,
        generate_audio: bool = False,
        seed: int = 0,
    ) -> IO.NodeOutput:
        _ = seed
        if model_name == "kling-video-o1":
            if duration > 10:
                raise ValueError("kling-video-o1 does not support durations greater than 10 seconds.")
            if generate_audio:
                raise ValueError("kling-video-o1 does not support audio generation.")
        stories_enabled = storyboards is not None and storyboards["storyboards"] != "disabled"
        if stories_enabled and model_name == "kling-video-o1":
            raise ValueError("kling-video-o1 does not support storyboards.")
        prompt = normalize_omni_prompt_references(prompt)
        validate_string(prompt, strip_whitespace=True, min_length=0 if stories_enabled else 1, max_length=2500)

        multi_shot = None
        multi_prompt_list = None
        if stories_enabled:
            count = int(storyboards["storyboards"].split()[0])
            multi_shot = True
            multi_prompt_list = []
            for i in range(1, count + 1):
                sb_prompt = storyboards[f"storyboard_{i}_prompt"]
                sb_duration = storyboards[f"storyboard_{i}_duration"]
                validate_string(sb_prompt, field_name=f"storyboard_{i}_prompt", min_length=1, max_length=512)
                multi_prompt_list.append(
                    MultiPromptEntry(
                        index=i,
                        prompt=sb_prompt,
                        duration=str(sb_duration),
                    )
                )
            total_storyboard_duration = sum(int(e.duration) for e in multi_prompt_list)
            if total_storyboard_duration != duration:
                raise ValueError(
                    f"Total storyboard duration ({total_storyboard_duration}s) "
                    f"must equal the global duration ({duration}s)."
                )

        if get_number_of_images(reference_images) > 7:
            raise ValueError("The maximum number of reference images is 7.")
        for i in reference_images:
            validate_image_dimensions(i, min_width=300, min_height=300)
            validate_image_aspect_ratio(i, (1, 2.5), (2.5, 1))
        image_list: list[OmniParamImage] = []
        for i in await upload_images_to_comfyapi(cls, reference_images, wait_label="Uploading reference image"):
            image_list.append(OmniParamImage(image_url=i))
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/kling/v1/videos/omni-video", method="POST"),
            response_model=TaskStatusResponse,
            data=OmniProReferences2VideoRequest(
                model_name=model_name,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=str(duration),
                image_list=image_list,
                mode="pro" if resolution == "1080p" else "std",
                sound="on" if generate_audio else "off",
                multi_shot=multi_shot,
                multi_prompt=multi_prompt_list,
                shot_type="customize" if multi_shot else None,
            ),
        )
        return await finish_omni_video_task(cls, response)