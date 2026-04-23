async def execute(
        cls,
        prompt: str,
        model: str,
        seed: int,
        images: Input.Image | None = None,
        audio: Input.Audio | None = None,
        video: Input.Video | None = None,
        files: list[GeminiPart] | None = None,
        system_prompt: str = "",
    ) -> IO.NodeOutput:
        if model == "gemini-3-pro-preview":
            model = "gemini-3.1-pro-preview"  # model "gemini-3-pro-preview" will be soon deprecated by Google
        elif model == "gemini-3-1-pro":
            model = "gemini-3.1-pro-preview"
        elif model == "gemini-3-1-flash-lite":
            model = "gemini-3.1-flash-lite-preview"

        parts: list[GeminiPart] = [GeminiPart(text=prompt)]
        if images is not None:
            parts.extend(await create_image_parts(cls, images))
        if audio is not None:
            parts.extend(cls.create_audio_parts(audio))
        if video is not None:
            parts.extend(cls.create_video_parts(video))
        if files is not None:
            parts.extend(files)

        gemini_system_prompt = None
        if system_prompt:
            gemini_system_prompt = GeminiSystemInstructionContent(parts=[GeminiTextPart(text=system_prompt)], role=None)

        response = await sync_op(
            cls,
            endpoint=ApiEndpoint(path=f"{GEMINI_BASE_ENDPOINT}/{model}", method="POST"),
            data=GeminiGenerateContentRequest(
                contents=[
                    GeminiContent(
                        role=GeminiRole.user,
                        parts=parts,
                    )
                ],
                systemInstruction=gemini_system_prompt,
            ),
            response_model=GeminiGenerateContentResponse,
            price_extractor=calculate_tokens_price,
        )

        output_text = get_text_from_response(response)
        return IO.NodeOutput(output_text or "Empty response from Gemini model...")