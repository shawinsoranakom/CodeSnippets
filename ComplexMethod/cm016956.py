async def execute(
        cls,
        model: str,
        prompt: str,
        image: Input.Image | None = None,
        size_preset: str = RECOMMENDED_PRESETS_SEEDREAM_4[0][0],
        width: int = 2048,
        height: int = 2048,
        sequential_image_generation: str = "disabled",
        max_images: int = 1,
        seed: int = 0,
        watermark: bool = False,
        fail_on_partial: bool = True,
    ) -> IO.NodeOutput:
        model = SEEDREAM_MODELS[model]
        validate_string(prompt, strip_whitespace=True, min_length=1)
        w = h = None
        for label, tw, th in RECOMMENDED_PRESETS_SEEDREAM_4:
            if label == size_preset:
                w, h = tw, th
                break

        if w is None or h is None:
            w, h = width, height

        out_num_pixels = w * h
        mp_provided = out_num_pixels / 1_000_000.0
        if ("seedream-4-5" in model or "seedream-5-0" in model) and out_num_pixels < 3686400:
            raise ValueError(
                f"Minimum image resolution for the selected model is 3.68MP, " f"but {mp_provided:.2f}MP provided."
            )
        if "seedream-4-0" in model and out_num_pixels < 921600:
            raise ValueError(
                f"Minimum image resolution that the selected model can generate is 0.92MP, "
                f"but {mp_provided:.2f}MP provided."
            )
        max_pixels = 10_404_496 if "seedream-5-0" in model else 16_777_216
        if out_num_pixels > max_pixels:
            raise ValueError(
                f"Maximum image resolution for the selected model is {max_pixels / 1_000_000:.2f}MP, "
                f"but {mp_provided:.2f}MP provided."
            )
        n_input_images = get_number_of_images(image) if image is not None else 0
        max_num_of_images = 14 if model == "seedream-5-0-260128" else 10
        if n_input_images > max_num_of_images:
            raise ValueError(
                f"Maximum of {max_num_of_images} reference images are supported, but {n_input_images} received."
            )
        if sequential_image_generation == "auto" and n_input_images + max_images > 15:
            raise ValueError(
                "The maximum number of generated images plus the number of reference images cannot exceed 15."
            )
        reference_images_urls = []
        if n_input_images:
            for i in image:
                validate_image_aspect_ratio(i, (1, 3), (3, 1))
            reference_images_urls = await upload_images_to_comfyapi(
                cls,
                image,
                max_images=n_input_images,
                mime_type="image/png",
            )
        response = await sync_op(
            cls,
            ApiEndpoint(path=BYTEPLUS_IMAGE_ENDPOINT, method="POST"),
            response_model=ImageTaskCreationResponse,
            data=Seedream4TaskCreationRequest(
                model=model,
                prompt=prompt,
                image=reference_images_urls,
                size=f"{w}x{h}",
                seed=seed,
                sequential_image_generation=sequential_image_generation,
                sequential_image_generation_options=Seedream4Options(max_images=max_images),
                watermark=watermark,
                output_format="png" if model == "seedream-5-0-260128" else None,
            ),
        )
        if len(response.data) == 1:
            return IO.NodeOutput(await download_url_to_image_tensor(get_image_url_from_response(response)))
        urls = [str(d["url"]) for d in response.data if isinstance(d, dict) and "url" in d]
        if fail_on_partial and len(urls) < len(response.data):
            raise RuntimeError(f"Only {len(urls)} of {len(response.data)} images were generated before error.")
        return IO.NodeOutput(torch.cat([await download_url_to_image_tensor(i) for i in urls]))