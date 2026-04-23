async def execute(
        cls,
        model: dict,
        seed: int,
        watermark: bool,
    ) -> IO.NodeOutput:
        validate_string(model["prompt"], strip_whitespace=True, min_length=1)

        reference_images = model.get("reference_images", {})
        reference_videos = model.get("reference_videos", {})
        reference_audios = model.get("reference_audios", {})
        reference_assets = model.get("reference_assets", {})

        reference_image_assets, reference_video_assets, reference_audio_assets = await _resolve_reference_assets(
            cls, list(reference_assets.values())
        )

        if not reference_images and not reference_videos and not reference_image_assets and not reference_video_assets:
            raise ValueError("At least one reference image or video or asset is required.")

        total_images = len(reference_images) + len(reference_image_assets)
        if total_images > 9:
            raise ValueError(
                f"Too many reference images: {total_images} "
                f"(images={len(reference_images)}, image assets={len(reference_image_assets)}). Maximum is 9."
            )
        total_videos = len(reference_videos) + len(reference_video_assets)
        if total_videos > 3:
            raise ValueError(
                f"Too many reference videos: {total_videos} "
                f"(videos={len(reference_videos)}, video assets={len(reference_video_assets)}). Maximum is 3."
            )
        total_audios = len(reference_audios) + len(reference_audio_assets)
        if total_audios > 3:
            raise ValueError(
                f"Too many reference audios: {total_audios} "
                f"(audios={len(reference_audios)}, audio assets={len(reference_audio_assets)}). Maximum is 3."
            )

        model_id = SEEDANCE_MODELS[model["model"]]
        has_video_input = total_videos > 0

        if model.get("auto_downscale") and reference_videos:
            max_px = SEEDANCE2_REF_VIDEO_PIXEL_LIMITS.get(model_id, {}).get(model["resolution"], {}).get("max")
            if max_px:
                for key in reference_videos:
                    reference_videos[key] = resize_video_to_pixel_budget(reference_videos[key], max_px)

        total_video_duration = 0.0
        for i, key in enumerate(reference_videos, 1):
            video = reference_videos[key]
            _validate_ref_video_pixels(video, model_id, model["resolution"], i)
            try:
                dur = video.get_duration()
                if dur < 1.8:
                    raise ValueError(f"Reference video {i} is too short: {dur:.1f}s. Minimum duration is 1.8 seconds.")
                total_video_duration += dur
            except ValueError:
                raise
            except Exception:
                pass
        if total_video_duration > 15.1:
            raise ValueError(f"Total reference video duration is {total_video_duration:.1f}s. Maximum is 15.1 seconds.")

        total_audio_duration = 0.0
        for i, key in enumerate(reference_audios, 1):
            audio = reference_audios[key]
            dur = int(audio["waveform"].shape[-1]) / int(audio["sample_rate"])
            if dur < 1.8:
                raise ValueError(f"Reference audio {i} is too short: {dur:.1f}s. Minimum duration is 1.8 seconds.")
            total_audio_duration += dur
        if total_audio_duration > 15.1:
            raise ValueError(f"Total reference audio duration is {total_audio_duration:.1f}s. Maximum is 15.1 seconds.")

        asset_labels = _build_asset_labels(
            reference_assets,
            reference_image_assets,
            reference_video_assets,
            reference_audio_assets,
            len(reference_images),
            len(reference_videos),
            len(reference_audios),
        )
        prompt_text = _rewrite_asset_refs(model["prompt"], asset_labels)

        content: list[TaskTextContent | TaskImageContent | TaskVideoContent | TaskAudioContent] = [
            TaskTextContent(text=prompt_text),
        ]
        for i, key in enumerate(reference_images, 1):
            content.append(
                TaskImageContent(
                    image_url=TaskImageContentUrl(
                        url=await upload_image_to_comfyapi(
                            cls,
                            image=reference_images[key],
                            wait_label=f"Uploading image {i}",
                        ),
                    ),
                    role="reference_image",
                ),
            )
        for i, key in enumerate(reference_videos, 1):
            content.append(
                TaskVideoContent(
                    video_url=TaskVideoContentUrl(
                        url=await upload_video_to_comfyapi(
                            cls,
                            reference_videos[key],
                            wait_label=f"Uploading video {i}",
                        ),
                    ),
                ),
            )
        for key in reference_audios:
            content.append(
                TaskAudioContent(
                    audio_url=TaskAudioContentUrl(
                        url=await upload_audio_to_comfyapi(
                            cls,
                            reference_audios[key],
                            container_format="mp3",
                            codec_name="libmp3lame",
                            mime_type="audio/mpeg",
                        ),
                    ),
                ),
            )
        for url in reference_image_assets.values():
            content.append(
                TaskImageContent(
                    image_url=TaskImageContentUrl(url=url),
                    role="reference_image",
                ),
            )
        for url in reference_video_assets.values():
            content.append(
                TaskVideoContent(video_url=TaskVideoContentUrl(url=url)),
            )
        for url in reference_audio_assets.values():
            content.append(
                TaskAudioContent(audio_url=TaskAudioContentUrl(url=url)),
            )
        initial_response = await sync_op(
            cls,
            ApiEndpoint(path=BYTEPLUS_TASK_ENDPOINT, method="POST"),
            data=Seedance2TaskCreationRequest(
                model=model_id,
                content=content,
                generate_audio=model["generate_audio"],
                resolution=model["resolution"],
                ratio=model["ratio"],
                duration=model["duration"],
                seed=seed,
                watermark=watermark,
            ),
            response_model=TaskCreationResponse,
        )
        response = await poll_op(
            cls,
            ApiEndpoint(path=f"{BYTEPLUS_SEEDANCE2_TASK_STATUS_ENDPOINT}/{initial_response.id}"),
            response_model=TaskStatusResponse,
            status_extractor=lambda r: r.status,
            price_extractor=_seedance2_price_extractor(model_id, has_video_input=has_video_input),
            poll_interval=9,
            max_poll_attempts=180,
        )
        return IO.NodeOutput(await download_url_to_video_output(response.content.video_url))