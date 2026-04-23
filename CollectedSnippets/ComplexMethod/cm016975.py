async def execute(
        cls,
        model_name: str,
        prompt: str,
        resolution: str,
        aspect_ratio: str,
        series_amount: str = "disabled",
        reference_images: Input.Image | None = None,
        seed: int = 0,
    ) -> IO.NodeOutput:
        _ = seed
        if model_name == "kling-image-o1" and resolution == "4K":
            raise ValueError("4K resolution is not supported for kling-image-o1 model.")
        prompt = normalize_omni_prompt_references(prompt)
        validate_string(prompt, min_length=1, max_length=2500)
        image_list: list[OmniImageParamImage] = []
        if reference_images is not None:
            if get_number_of_images(reference_images) > 10:
                raise ValueError("The maximum number of reference images is 10.")
            for i in reference_images:
                validate_image_dimensions(i, min_width=300, min_height=300)
                validate_image_aspect_ratio(i, (1, 2.5), (2.5, 1))
            for i in await upload_images_to_comfyapi(cls, reference_images, wait_label="Uploading reference image"):
                image_list.append(OmniImageParamImage(image=i))
        use_series = series_amount != "disabled"
        if use_series and model_name == "kling-image-o1":
            raise ValueError("kling-image-o1 does not support series generation.")
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/kling/v1/images/omni-image", method="POST"),
            response_model=TaskStatusResponse,
            data=OmniProImageRequest(
                model_name=model_name,
                prompt=prompt,
                resolution=resolution.lower(),
                aspect_ratio=aspect_ratio,
                image_list=image_list if image_list else None,
                result_type="series" if use_series else None,
                series_amount=int(series_amount) if use_series else None,
            ),
        )
        if response.code:
            raise RuntimeError(
                f"Kling request failed. Code: {response.code}, Message: {response.message}, Data: {response.data}"
            )
        final_response = await poll_op(
            cls,
            ApiEndpoint(path=f"/proxy/kling/v1/images/omni-image/{response.data.task_id}"),
            response_model=TaskStatusResponse,
            status_extractor=lambda r: (r.data.task_status if r.data else None),
        )
        images = final_response.data.task_result.series_images or final_response.data.task_result.images
        tensors = [await download_url_to_image_tensor(img.url) for img in images]
        return IO.NodeOutput(torch.cat(tensors, dim=0))