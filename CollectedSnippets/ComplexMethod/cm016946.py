async def execute(
        cls,
        prompt: str,
        negative_prompt: str,
        resolution: str,
        aspect_ratio: str,
        duration: int,
        seed: int,
        first_frame: Input.Image,
        last_frame: Input.Image,
        model: str,
        generate_audio: bool,
    ):
        if "lite" in model and resolution == "4k":
            raise Exception("4K resolution is not supported by the veo-3.1-lite model.")

        model = MODELS_MAP[model]
        initial_response = await sync_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/generate", method="POST"),
            response_model=VeoGenVidResponse,
            data=VeoGenVidRequest(
                instances=[
                    VeoRequestInstance(
                        prompt=prompt,
                        image=VeoRequestInstanceImage(
                            bytesBase64Encoded=tensor_to_base64_string(first_frame), mimeType="image/png"
                        ),
                        lastFrame=VeoRequestInstanceImage(
                            bytesBase64Encoded=tensor_to_base64_string(last_frame), mimeType="image/png"
                        ),
                    ),
                ],
                parameters=VeoRequestParameters(
                    aspectRatio=aspect_ratio,
                    personGeneration="ALLOW",
                    durationSeconds=duration,
                    enhancePrompt=True,  # cannot be False for Veo3
                    seed=seed,
                    generateAudio=generate_audio,
                    negativePrompt=negative_prompt,
                    resolution=resolution,
                ),
            ),
        )
        poll_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/poll", method="POST"),
            response_model=VeoGenVidPollResponse,
            status_extractor=lambda r: "completed" if r.done else "pending",
            data=VeoGenVidPollRequest(
                operationName=initial_response.name,
            ),
            poll_interval=9.0,
            estimated_duration=AVERAGE_DURATION_VIDEO_GEN,
        )

        if poll_response.error:
            raise Exception(f"Veo API error: {poll_response.error.message} (code: {poll_response.error.code})")

        response = poll_response.response
        filtered_count = response.raiMediaFilteredCount
        if filtered_count:
            reasons = response.raiMediaFilteredReasons or []
            reason_part = f": {reasons[0]}" if reasons else ""
            raise Exception(
                f"Content blocked by Google's Responsible AI filters{reason_part} "
                f"({filtered_count} video{'s' if filtered_count != 1 else ''} filtered)."
            )

        if response.videos:
            video = response.videos[0]
            if video.bytesBase64Encoded:
                return IO.NodeOutput(InputImpl.VideoFromFile(BytesIO(base64.b64decode(video.bytesBase64Encoded))))
            if video.gcsUri:
                return IO.NodeOutput(await download_url_to_video_output(video.gcsUri))
            raise Exception("Video returned but no data or URL was provided")
        raise Exception("Video generation completed but no video was returned")