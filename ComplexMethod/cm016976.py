async def execute(
        cls,
        multi_shot: dict,
        generate_audio: bool,
        model: dict,
        seed: int,
        start_frame: Input.Image | None = None,
    ) -> IO.NodeOutput:
        _ = seed
        mode = "pro" if model["resolution"] == "1080p" else "std"
        custom_multi_shot = False
        if multi_shot["multi_shot"] == "disabled":
            shot_type = None
        else:
            shot_type = "customize"
            custom_multi_shot = True

        multi_prompt_list = None
        if shot_type == "customize":
            count = int(multi_shot["multi_shot"].split()[0])
            multi_prompt_list = []
            for i in range(1, count + 1):
                sb_prompt = multi_shot[f"storyboard_{i}_prompt"]
                sb_duration = multi_shot[f"storyboard_{i}_duration"]
                validate_string(sb_prompt, field_name=f"storyboard_{i}_prompt", min_length=1, max_length=512)
                multi_prompt_list.append(
                    MultiPromptEntry(
                        index=i,
                        prompt=sb_prompt,
                        duration=str(sb_duration),
                    )
                )
            duration = sum(int(e.duration) for e in multi_prompt_list)
            if duration < 3 or duration > 15:
                raise ValueError(
                    f"Total storyboard duration ({duration}s) must be between 3 and 15 seconds."
                )
        else:
            duration = multi_shot["duration"]
            validate_string(multi_shot["prompt"], min_length=1, max_length=2500)

        if start_frame is not None:
            validate_image_dimensions(start_frame, min_width=300, min_height=300)
            validate_image_aspect_ratio(start_frame, (1, 2.5), (2.5, 1))
            image_url = await upload_image_to_comfyapi(cls, start_frame, wait_label="Uploading start frame")
            response = await sync_op(
                cls,
                ApiEndpoint(path="/proxy/kling/v1/videos/image2video", method="POST"),
                response_model=TaskStatusResponse,
                data=ImageToVideoWithAudioRequest(
                    model_name=model["model"],
                    image=image_url,
                    prompt=None if custom_multi_shot else multi_shot["prompt"],
                    negative_prompt=None if custom_multi_shot else multi_shot["negative_prompt"],
                    mode=mode,
                    duration=str(duration),
                    sound="on" if generate_audio else "off",
                    multi_shot=True if shot_type else None,
                    multi_prompt=multi_prompt_list,
                    shot_type=shot_type,
                ),
            )
            poll_path = f"/proxy/kling/v1/videos/image2video/{response.data.task_id}"
        else:
            response = await sync_op(
                cls,
                ApiEndpoint(path="/proxy/kling/v1/videos/text2video", method="POST"),
                response_model=TaskStatusResponse,
                data=TextToVideoWithAudioRequest(
                    model_name=model["model"],
                    aspect_ratio=model["aspect_ratio"],
                    prompt=None if custom_multi_shot else multi_shot["prompt"],
                    negative_prompt=None if custom_multi_shot else multi_shot["negative_prompt"],
                    mode=mode,
                    duration=str(duration),
                    sound="on" if generate_audio else "off",
                    multi_shot=True if shot_type else None,
                    multi_prompt=multi_prompt_list,
                    shot_type=shot_type,
                ),
            )
            poll_path = f"/proxy/kling/v1/videos/text2video/{response.data.task_id}"

        if response.code:
            raise RuntimeError(
                f"Kling request failed. Code: {response.code}, Message: {response.message}, Data: {response.data}"
            )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=poll_path),
            response_model=TaskStatusResponse,
            status_extractor=lambda r: (r.data.task_status if r.data else None),
        )
        return IO.NodeOutput(await download_url_to_video_output(final_response.data.task_result.videos[0].url))