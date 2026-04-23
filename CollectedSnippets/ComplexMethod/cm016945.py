async def execute(
        cls,
        prompt,
        aspect_ratio="16:9",
        resolution="720p",
        negative_prompt="",
        duration_seconds=8,
        enhance_prompt=True,
        person_generation="ALLOW",
        seed=0,
        image=None,
        model="veo-3.0-generate-001",
        generate_audio=False,
    ):
        if resolution == "4k" and ("lite" in model or "3.0" in model):
            raise Exception("4K resolution is not supported by the veo-3.1-lite or veo-3.0 models.")

        model = MODELS_MAP[model]

        instances = [{"prompt": prompt}]
        if image is not None:
            image_base64 = tensor_to_base64_string(image)
            if image_base64:
                instances[0]["image"] = {"bytesBase64Encoded": image_base64, "mimeType": "image/png"}

        parameters = {
            "aspectRatio": aspect_ratio,
            "personGeneration": person_generation,
            "durationSeconds": duration_seconds,
            "enhancePrompt": True,
            "generateAudio": generate_audio,
        }
        if negative_prompt:
            parameters["negativePrompt"] = negative_prompt
        if seed > 0:
            parameters["seed"] = seed
        if "veo-3.1" in model:
            parameters["resolution"] = resolution

        initial_response = await sync_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/generate", method="POST"),
            response_model=VeoGenVidResponse,
            data=VeoGenVidRequest(
                instances=instances,
                parameters=parameters,
            ),
        )

        poll_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/poll", method="POST"),
            response_model=VeoGenVidPollResponse,
            status_extractor=lambda r: "completed" if r.done else "pending",
            data=VeoGenVidPollRequest(operationName=initial_response.name),
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