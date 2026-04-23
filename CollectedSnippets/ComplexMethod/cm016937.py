async def execute(
        cls,
        model: str,
        image: Input.Image,
        prompt: str,
        negative_prompt: str = "",
        resolution: str = "720P",
        duration: int = 5,
        audio: Input.Audio | None = None,
        seed: int = 0,
        generate_audio: bool = False,
        prompt_extend: bool = True,
        watermark: bool = False,
        shot_type: str = "single",
    ):
        if get_number_of_images(image) != 1:
            raise ValueError("Exactly one input image is required.")
        if "480P" in resolution and model == "wan2.6-i2v":
            raise ValueError("The Wan 2.6 model does not support 480P.")
        if duration == 15 and model == "wan2.5-i2v-preview":
            raise ValueError("A 15-second duration is supported only by the Wan 2.6 model.")
        image_url = "data:image/png;base64," + tensor_to_base64_string(image, total_pixels=2000 * 2000)
        audio_url = None
        if audio is not None:
            validate_audio_duration(audio, 3.0, 29.0)
            audio_url = "data:audio/mp3;base64," + audio_to_base64_string(audio, "mp3", "libmp3lame")
        initial_response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/wan/api/v1/services/aigc/video-generation/video-synthesis", method="POST"),
            response_model=TaskCreationResponse,
            data=Image2VideoTaskCreationRequest(
                model=model,
                input=Image2VideoInputField(
                    prompt=prompt, negative_prompt=negative_prompt, img_url=image_url, audio_url=audio_url
                ),
                parameters=Image2VideoParametersField(
                    resolution=resolution,
                    duration=duration,
                    seed=seed,
                    audio=generate_audio,
                    prompt_extend=prompt_extend,
                    watermark=watermark,
                    shot_type=shot_type,
                ),
            ),
        )
        if not initial_response.output:
            raise Exception(f"An unknown error occurred: {initial_response.code} - {initial_response.message}")
        response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/wan/api/v1/tasks/{initial_response.output.task_id}"),
            response_model=VideoTaskStatusResponse,
            status_extractor=lambda x: x.output.task_status,
            estimated_duration=120 * int(duration / 5),
            poll_interval=6,
        )
        return IO.NodeOutput(await download_url_to_video_output(response.output.video_url))