async def execute(
        cls,
        prompt: str,
        model: str,
        seed: int,
        aspect_ratio: str,
        resolution: str,
        response_modalities: str,
        images: Input.Image | None = None,
        files: list[GeminiPart] | None = None,
        system_prompt: str = "",
    ) -> IO.NodeOutput:
        validate_string(prompt, strip_whitespace=True, min_length=1)
        if model == "Nano Banana 2 (Gemini 3.1 Flash Image)":
            model = "gemini-3.1-flash-image-preview"

        parts: list[GeminiPart] = [GeminiPart(text=prompt)]
        if images is not None:
            if get_number_of_images(images) > 14:
                raise ValueError("The current maximum number of supported images is 14.")
            parts.extend(await create_image_parts(cls, images))
        if files is not None:
            parts.extend(files)

        image_config = GeminiImageConfig(imageSize=resolution)
        if aspect_ratio != "auto":
            image_config.aspectRatio = aspect_ratio

        gemini_system_prompt = None
        if system_prompt:
            gemini_system_prompt = GeminiSystemInstructionContent(parts=[GeminiTextPart(text=system_prompt)], role=None)

        response = await sync_op(
            cls,
            ApiEndpoint(path=f"/proxy/vertexai/gemini/{model}", method="POST"),
            data=GeminiImageGenerateContentRequest(
                contents=[
                    GeminiContent(role=GeminiRole.user, parts=parts),
                ],
                generationConfig=GeminiImageGenerationConfig(
                    responseModalities=(["IMAGE"] if response_modalities == "IMAGE" else ["TEXT", "IMAGE"]),
                    imageConfig=image_config,
                ),
                systemInstruction=gemini_system_prompt,
            ),
            response_model=GeminiGenerateContentResponse,
            price_extractor=calculate_tokens_price,
        )
        return IO.NodeOutput(await get_image_from_response(response), get_text_from_response(response))