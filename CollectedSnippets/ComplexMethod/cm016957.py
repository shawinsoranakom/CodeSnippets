async def execute(
        cls,
        model: dict,
        seed: int,
        watermark: bool,
        first_frame: Input.Image | None = None,
        last_frame: Input.Image | None = None,
        first_frame_asset_id: str = "",
        last_frame_asset_id: str = "",
    ) -> IO.NodeOutput:
        validate_string(model["prompt"], strip_whitespace=True, min_length=1)
        model_id = SEEDANCE_MODELS[model["model"]]

        first_frame_asset_id = first_frame_asset_id.strip()
        last_frame_asset_id = last_frame_asset_id.strip()

        if first_frame is not None and first_frame_asset_id:
            raise ValueError("Provide only one of first_frame or first_frame_asset_id, not both.")
        if first_frame is None and not first_frame_asset_id:
            raise ValueError("Either first_frame or first_frame_asset_id is required.")
        if last_frame is not None and last_frame_asset_id:
            raise ValueError("Provide only one of last_frame or last_frame_asset_id, not both.")

        asset_ids_to_resolve = [a for a in (first_frame_asset_id, last_frame_asset_id) if a]
        image_assets: dict[str, str] = {}
        if asset_ids_to_resolve:
            image_assets, _, _ = await _resolve_reference_assets(cls, asset_ids_to_resolve)
            for aid in asset_ids_to_resolve:
                if aid not in image_assets:
                    raise ValueError(f"Asset {aid} is not an Image asset.")

        if first_frame_asset_id:
            first_frame_url = image_assets[first_frame_asset_id]
        else:
            first_frame_url = await upload_image_to_comfyapi(cls, first_frame, wait_label="Uploading first frame.")

        content: list[TaskTextContent | TaskImageContent] = [
            TaskTextContent(text=model["prompt"]),
            TaskImageContent(
                image_url=TaskImageContentUrl(url=first_frame_url),
                role="first_frame",
            ),
        ]
        if last_frame_asset_id:
            content.append(
                TaskImageContent(
                    image_url=TaskImageContentUrl(url=image_assets[last_frame_asset_id]),
                    role="last_frame",
                ),
            )
        elif last_frame is not None:
            content.append(
                TaskImageContent(
                    image_url=TaskImageContentUrl(
                        url=await upload_image_to_comfyapi(cls, last_frame, wait_label="Uploading last frame.")
                    ),
                    role="last_frame",
                ),
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
            price_extractor=_seedance2_price_extractor(model_id, has_video_input=False),
            poll_interval=9,
            max_poll_attempts=180,
        )
        return IO.NodeOutput(await download_url_to_video_output(response.content.video_url))