async def execute_image2video(
    cls: type[IO.ComfyNode],
    start_frame: torch.Tensor,
    prompt: str,
    negative_prompt: str,
    model_name: str,
    cfg_scale: float,
    model_mode: str,
    aspect_ratio: str,
    duration: str,
    camera_control: KlingCameraControl | None = None,
    end_frame: torch.Tensor | None = None,
) -> IO.NodeOutput:
    validate_prompts(prompt, negative_prompt, MAX_PROMPT_LENGTH_I2V)
    validate_input_image(start_frame)

    if camera_control is not None:
        # Camera control type for image 2 video is always `simple`
        camera_control.type = KlingCameraControlType.simple

    if model_mode == "std" and model_name == KlingVideoGenModelName.kling_v2_5_turbo.value:
        model_mode = "pro"  # October 5: currently "std" mode is not supported for this model

    task_creation_response = await sync_op(
        cls,
        ApiEndpoint(path=PATH_IMAGE_TO_VIDEO, method="POST"),
        response_model=KlingImage2VideoResponse,
        data=KlingImage2VideoRequest(
            model_name=KlingVideoGenModelName(model_name),
            image=tensor_to_base64_string(start_frame),
            image_tail=(
                tensor_to_base64_string(end_frame)
                if end_frame is not None
                else None
            ),
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            cfg_scale=cfg_scale,
            mode=KlingVideoGenMode(model_mode),
            duration=KlingVideoGenDuration(duration),
            camera_control=camera_control,
        ),
    )

    validate_task_creation_response(task_creation_response)
    task_id = task_creation_response.data.task_id

    final_response = await poll_op(
        cls,
        ApiEndpoint(path=f"{PATH_IMAGE_TO_VIDEO}/{task_id}"),
        response_model=KlingImage2VideoResponse,
        estimated_duration=AVERAGE_DURATION_I2V,
        status_extractor=lambda r: (r.data.task_status.value if r.data and r.data.task_status else None),
    )
    validate_video_result_response(final_response)

    video = get_video_from_response(final_response)
    return IO.NodeOutput(await download_url_to_video_output(str(video.url)), str(video.id), str(video.duration))