async def execute(
        cls,
        video: Input.Video,
        upscaler_enabled: bool,
        upscaler_model: str,
        upscaler_resolution: str,
        upscaler_creativity: str = "low",
        interpolation_enabled: bool = False,
        interpolation_model: str = "apo-8",
        interpolation_slowmo: int = 1,
        interpolation_frame_rate: int = 60,
        interpolation_duplicate: bool = False,
        interpolation_duplicate_threshold: float = 0.01,
        dynamic_compression_level: str = "Low",
    ) -> IO.NodeOutput:
        if upscaler_enabled is False and interpolation_enabled is False:
            raise ValueError("There is nothing to do: both upscaling and interpolation are disabled.")
        validate_container_format_is_mp4(video)
        src_width, src_height = video.get_dimensions()
        src_frame_rate = int(video.get_frame_rate())
        duration_sec = video.get_duration()
        src_video_stream = video.get_stream_source()
        target_width = src_width
        target_height = src_height
        target_frame_rate = src_frame_rate
        filters = []
        if upscaler_enabled:
            if "1080p" in upscaler_resolution:
                target_pixel_p = 1080
                max_long_side = 1920
            else:
                target_pixel_p = 2160
                max_long_side = 3840
            ar = src_width / src_height
            if src_width >= src_height:
                # Landscape or Square; Attempt to set height to target (e.g., 2160), calculate width
                target_height = target_pixel_p
                target_width = int(target_height * ar)
                # Check if width exceeds standard bounds (for ultra-wide e.g., 21:9 ARs)
                if target_width > max_long_side:
                    target_width = max_long_side
                    target_height = int(target_width / ar)
            else:
                # Portrait; Attempt to set width to target (e.g., 2160), calculate height
                target_width = target_pixel_p
                target_height = int(target_width / ar)
                # Check if height exceeds standard bounds
                if target_height > max_long_side:
                    target_height = max_long_side
                    target_width = int(target_height * ar)
            if target_width % 2 != 0:
                target_width += 1
            if target_height % 2 != 0:
                target_height += 1
            filters.append(
                VideoEnhancementFilter(
                    model=UPSCALER_MODELS_MAP[upscaler_model],
                    creativity=(upscaler_creativity if UPSCALER_MODELS_MAP[upscaler_model] == "slc-1" else None),
                    isOptimizedMode=(True if UPSCALER_MODELS_MAP[upscaler_model] == "slc-1" else None),
                ),
            )
        if interpolation_enabled:
            target_frame_rate = interpolation_frame_rate
            filters.append(
                VideoFrameInterpolationFilter(
                    model=interpolation_model,
                    slowmo=interpolation_slowmo,
                    fps=interpolation_frame_rate,
                    duplicate=interpolation_duplicate,
                    duplicate_threshold=interpolation_duplicate_threshold,
                ),
            )
        initial_res = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/topaz/video/", method="POST"),
            response_model=CreateVideoResponse,
            data=CreateVideoRequest(
                source=CreateVideoRequestSource(
                    container="mp4",
                    size=get_fs_object_size(src_video_stream),
                    duration=int(duration_sec),
                    frameCount=video.get_frame_count(),
                    frameRate=src_frame_rate,
                    resolution=Resolution(width=src_width, height=src_height),
                ),
                filters=filters,
                output=OutputInformationVideo(
                    resolution=Resolution(width=target_width, height=target_height),
                    frameRate=target_frame_rate,
                    audioCodec="AAC",
                    audioTransfer="Copy",
                    dynamicCompressionLevel=dynamic_compression_level,
                ),
            ),
            wait_label="Creating task",
            final_label_on_success="Task created",
        )
        upload_res = await sync_op(
            cls,
            ApiEndpoint(
                path=f"/proxy/topaz/video/{initial_res.requestId}/accept",
                method="PATCH",
            ),
            response_model=VideoAcceptResponse,
            wait_label="Preparing upload",
            final_label_on_success="Upload started",
        )
        if len(upload_res.urls) > 1:
            raise NotImplementedError(
                "Large files are not currently supported. Please open an issue in the ComfyUI repository."
            )
        async with aiohttp.ClientSession(headers={"Content-Type": "video/mp4"}) as session:
            if isinstance(src_video_stream, BytesIO):
                src_video_stream.seek(0)
                async with session.put(upload_res.urls[0], data=src_video_stream, raise_for_status=True) as res:
                    upload_etag = res.headers["Etag"]
            else:
                with builtins.open(src_video_stream, "rb") as video_file:
                    async with session.put(upload_res.urls[0], data=video_file, raise_for_status=True) as res:
                        upload_etag = res.headers["Etag"]
        await sync_op(
            cls,
            ApiEndpoint(
                path=f"/proxy/topaz/video/{initial_res.requestId}/complete-upload",
                method="PATCH",
            ),
            response_model=VideoCompleteUploadResponse,
            data=VideoCompleteUploadRequest(
                uploadResults=[
                    VideoCompleteUploadRequestPart(
                        partNum=1,
                        eTag=upload_etag,
                    ),
                ],
            ),
            wait_label="Finalizing upload",
            final_label_on_success="Upload completed",
        )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/topaz/video/{initial_res.requestId}/status"),
            response_model=VideoStatusResponse,
            status_extractor=lambda x: x.status,
            progress_extractor=lambda x: getattr(x, "progress", 0),
            price_extractor=lambda x: (x.estimates.cost[0] * 0.08 if x.estimates and x.estimates.cost[0] else None),
            poll_interval=10.0,
            max_poll_attempts=320,
        )
        return IO.NodeOutput(await download_url_to_video_output(final_response.download.url))