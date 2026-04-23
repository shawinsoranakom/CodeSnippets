async def execute(
        cls,
        model: str,
        image: Input.Image,
        face_count: int,
        generate_type: InputGenerateType,
        seed: int,
        image_left: Input.Image | None = None,
        image_right: Input.Image | None = None,
        image_back: Input.Image | None = None,
    ) -> IO.NodeOutput:
        _ = seed
        if model == "3.1" and generate_type["generate_type"].lower() == "lowpoly":
            raise ValueError("The LowPoly option is currently unavailable for the 3.1 model.")
        validate_image_dimensions(image, min_width=128, min_height=128)
        multiview_images = []
        for k, v in {
            "left": image_left,
            "right": image_right,
            "back": image_back,
        }.items():
            if v is None:
                continue
            validate_image_dimensions(v, min_width=128, min_height=128)
            multiview_images.append(
                Hunyuan3DViewImage(
                    ViewType=k,
                    ViewImageUrl=await upload_image_to_comfyapi(
                        cls,
                        downscale_image_tensor_by_max_side(v, max_side=4900),
                        mime_type="image/webp",
                        total_pixels=24_010_000,
                    ),
                )
            )
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/tencent/hunyuan/3d-pro", method="POST"),
            response_model=To3DProTaskCreateResponse,
            data=To3DProTaskRequest(
                Model=model,
                FaceCount=face_count,
                GenerateType=generate_type["generate_type"],
                ImageUrl=await upload_image_to_comfyapi(
                    cls,
                    downscale_image_tensor_by_max_side(image, max_side=4900),
                    mime_type="image/webp",
                    total_pixels=24_010_000,
                ),
                MultiViewImages=multiview_images if multiview_images else None,
                EnablePBR=generate_type.get("pbr", None),
                PolygonType=generate_type.get("polygon_type", None),
            ),
            is_rate_limited=_is_tencent_rate_limited,
        )
        if response.Error:
            raise ValueError(f"Task creation failed with code {response.Error.Code}: {response.Error.Message}")
        task_id = response.JobId
        result = await poll_op(
            cls,
            ApiEndpoint(path="/proxy/tencent/hunyuan/3d-pro/query", method="POST"),
            data=To3DProTaskQueryRequest(JobId=task_id),
            response_model=To3DProTaskResultResponse,
            status_extractor=lambda r: r.Status,
        )
        obj_file_response = get_file_from_response(result.ResultFile3Ds, "obj", raise_if_not_found=False)
        if obj_file_response:
            obj_result = await download_and_extract_obj_zip(obj_file_response.Url)
            return IO.NodeOutput(
                f"{task_id}.glb",
                await download_url_to_file_3d(
                    get_file_from_response(result.ResultFile3Ds, "glb").Url, "glb", task_id=task_id
                ),
                obj_result.obj,
                obj_result.texture,
                obj_result.metallic if obj_result.metallic is not None else torch.zeros(1, 1, 1, 3),
                obj_result.normal if obj_result.normal is not None else torch.zeros(1, 1, 1, 3),
                obj_result.roughness if obj_result.roughness is not None else torch.zeros(1, 1, 1, 3),
            )
        return IO.NodeOutput(
            f"{task_id}.glb",
            await download_url_to_file_3d(
                get_file_from_response(result.ResultFile3Ds, "glb").Url, "glb", task_id=task_id
            ),
            None,
            None,
            None,
            None,
            None,
        )