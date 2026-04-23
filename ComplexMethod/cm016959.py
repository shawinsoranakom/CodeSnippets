async def execute(
        cls,
        model: str,
        image: Input.Image,
        prompt: str,
        resolution: str,
        number_of_images: int,
        seed: int,
        aspect_ratio: str = "auto",
    ) -> IO.NodeOutput:
        validate_string(prompt, strip_whitespace=True, min_length=1)
        if model == "grok-imagine-image-pro":
            if get_number_of_images(image) > 1:
                raise ValueError("The pro model supports only 1 input image.")
        elif get_number_of_images(image) > 3:
            raise ValueError("A maximum of 3 input images is supported.")
        if aspect_ratio != "auto" and get_number_of_images(image) == 1:
            raise ValueError(
                "Custom aspect ratio is only allowed when multiple images are connected to the image input."
            )
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/xai/v1/images/edits", method="POST"),
            data=ImageEditRequest(
                model=model,
                images=[InputUrlObject(url=f"data:image/png;base64,{tensor_to_base64_string(i)}") for i in image],
                prompt=prompt,
                resolution=resolution.lower(),
                n=number_of_images,
                seed=seed,
                aspect_ratio=None if aspect_ratio == "auto" else aspect_ratio,
            ),
            response_model=ImageGenerationResponse,
            price_extractor=_extract_grok_price,
        )
        if len(response.data) == 1:
            return IO.NodeOutput(await download_url_to_image_tensor(response.data[0].url))
        return IO.NodeOutput(
            torch.cat(
                [await download_url_to_image_tensor(i) for i in [str(d.url) for d in response.data if d.url]],
            )
        )