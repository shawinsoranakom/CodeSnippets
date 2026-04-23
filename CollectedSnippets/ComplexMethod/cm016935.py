async def _generate_mm_video(
    cls: type[IO.ComfyNode],
    *,
    prompt_text: str,
    seed: int,
    model: str,
    image: Optional[torch.Tensor] = None,  # used for ImageToVideo
    subject: Optional[torch.Tensor] = None,  # used for SubjectToVideo
    average_duration: Optional[int] = None,
) -> IO.NodeOutput:
    if image is None:
        validate_string(prompt_text, field_name="prompt_text")
    image_url = None
    if image is not None:
        image_url = (await upload_images_to_comfyapi(cls, image, max_images=1))[0]

    # TODO: figure out how to deal with subject properly, API returns invalid params when using S2V-01 model
    subject_reference = None
    if subject is not None:
        subject_url = (await upload_images_to_comfyapi(cls, subject, max_images=1))[0]
        subject_reference = [SubjectReferenceItem(image=subject_url)]

    response = await sync_op(
        cls,
        ApiEndpoint(path="/proxy/minimax/video_generation", method="POST"),
        response_model=MinimaxVideoGenerationResponse,
        data=MinimaxVideoGenerationRequest(
            model=MiniMaxModel(model),
            prompt=prompt_text,
            callback_url=None,
            first_frame_image=image_url,
            subject_reference=subject_reference,
            prompt_optimizer=None,
        ),
    )

    task_id = response.task_id
    if not task_id:
        raise Exception(f"MiniMax generation failed: {response.base_resp}")

    task_result = await poll_op(
        cls,
        ApiEndpoint(path="/proxy/minimax/query/video_generation", query_params={"task_id": task_id}),
        response_model=MinimaxTaskResultResponse,
        status_extractor=lambda x: x.status.value,
        estimated_duration=average_duration,
    )

    file_id = task_result.file_id
    if file_id is None:
        raise Exception("Request was not successful. Missing file ID.")
    file_result = await sync_op(
        cls,
        ApiEndpoint(path="/proxy/minimax/files/retrieve", query_params={"file_id": int(file_id)}),
        response_model=MinimaxFileRetrieveResponse,
    )

    file_url = file_result.file.download_url
    if file_url is None:
        raise Exception(f"No video was found in the response. Full response: {file_result.model_dump()}")
    if file_result.file.backup_download_url:
        try:
            return IO.NodeOutput(await download_url_to_video_output(file_url, timeout=10, max_retries=2))
        except Exception:  # if we have a second URL to retrieve the result, try again using that one
            return IO.NodeOutput(
                await download_url_to_video_output(file_result.file.backup_download_url, max_retries=3)
            )
    return IO.NodeOutput(await download_url_to_video_output(file_url))