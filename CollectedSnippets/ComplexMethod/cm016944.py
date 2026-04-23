async def execute(
        cls,
        prompt,
        aspect_ratio="16:9",
        negative_prompt="",
        duration_seconds=5,
        enhance_prompt=True,
        person_generation="ALLOW",
        seed=0,
        image=None,
        model="veo-2.0-generate-001",
        generate_audio=False,
    ):
        model = MODELS_MAP[model]
        # Prepare the instances for the request
        instances = []

        instance = {"prompt": prompt}

        # Add image if provided
        if image is not None:
            image_base64 = tensor_to_base64_string(image)
            if image_base64:
                instance["image"] = {"bytesBase64Encoded": image_base64, "mimeType": "image/png"}

        instances.append(instance)

        # Create parameters dictionary
        parameters = {
            "aspectRatio": aspect_ratio,
            "personGeneration": person_generation,
            "durationSeconds": duration_seconds,
            "enhancePrompt": enhance_prompt,
        }

        # Add optional parameters if provided
        if negative_prompt:
            parameters["negativePrompt"] = negative_prompt
        if seed > 0:
            parameters["seed"] = seed
        # Only add generateAudio for Veo 3 models
        if model.find("veo-2.0") == -1:
            parameters["generateAudio"] = generate_audio
            # force "enhance_prompt" to True for Veo3 models
            parameters["enhancePrompt"] = True

        initial_response = await sync_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/generate", method="POST"),
            response_model=VeoGenVidResponse,
            data=VeoGenVidRequest(
                instances=instances,
                parameters=parameters,
            ),
        )

        def status_extractor(response):
            # Only return "completed" if the operation is done, regardless of success or failure
            # We'll check for errors after polling completes
            return "completed" if response.done else "pending"

        poll_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/veo/{model}/poll", method="POST"),
            response_model=VeoGenVidPollResponse,
            status_extractor=status_extractor,
            data=VeoGenVidPollRequest(
                operationName=initial_response.name,
            ),
            poll_interval=5.0,
            estimated_duration=AVERAGE_DURATION_VIDEO_GEN,
        )

        # Now check for errors in the final response
        # Check for error in poll response
        if poll_response.error:
            raise Exception(f"Veo API error: {poll_response.error.message} (code: {poll_response.error.code})")

        # Check for RAI filtered content
        if (
            hasattr(poll_response.response, "raiMediaFilteredCount")
            and poll_response.response.raiMediaFilteredCount > 0
        ):

            # Extract reason message if available
            if (
                hasattr(poll_response.response, "raiMediaFilteredReasons")
                and poll_response.response.raiMediaFilteredReasons
            ):
                reason = poll_response.response.raiMediaFilteredReasons[0]
                error_message = f"Content filtered by Google's Responsible AI practices: {reason} ({poll_response.response.raiMediaFilteredCount} videos filtered.)"
            else:
                error_message = f"Content filtered by Google's Responsible AI practices ({poll_response.response.raiMediaFilteredCount} videos filtered.)"

            raise Exception(error_message)

        # Extract video data
        if (
            poll_response.response
            and hasattr(poll_response.response, "videos")
            and poll_response.response.videos
            and len(poll_response.response.videos) > 0
        ):
            video = poll_response.response.videos[0]

            # Check if video is provided as base64 or URL
            if hasattr(video, "bytesBase64Encoded") and video.bytesBase64Encoded:
                return IO.NodeOutput(InputImpl.VideoFromFile(BytesIO(base64.b64decode(video.bytesBase64Encoded))))

            if hasattr(video, "gcsUri") and video.gcsUri:
                return IO.NodeOutput(await download_url_to_video_output(video.gcsUri))

            raise Exception("Video returned but no data or URL was provided")
        raise Exception("Video generation completed but no video was returned")