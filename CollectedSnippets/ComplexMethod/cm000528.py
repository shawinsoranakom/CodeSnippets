async def run_model(
        self,
        api_key: SecretStr,
        model: ImageEditorModel,
        prompt: str,
        input_image_b64: Optional[str],
        aspect_ratio: str,
        seed: Optional[int],
        user_id: str,
        graph_exec_id: str,
    ) -> MediaFileType:
        client = ReplicateClient(api_token=api_key.get_secret_value())
        model_name = model.api_name

        is_nano_banana = model in (
            ImageEditorModel.NANO_BANANA_PRO,
            ImageEditorModel.NANO_BANANA_2,
        )
        if is_nano_banana:
            input_params: dict = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": "jpg",
                "safety_filter_level": "block_only_high",
            }
            # NB API expects "image_input" as a list, unlike Flux's single "input_image"
            if input_image_b64:
                input_params["image_input"] = [input_image_b64]
        else:
            input_params = {
                "prompt": prompt,
                "input_image": input_image_b64,
                "aspect_ratio": aspect_ratio,
                **({"seed": seed} if seed is not None else {}),
            }

        try:
            output: FileOutput | list[FileOutput] = await client.async_run(  # type: ignore
                model_name,
                input=input_params,
                wait=False,
            )
        except Exception as e:
            if "flagged as sensitive" in str(e).lower():
                raise ModerationError(
                    message="Content was flagged as sensitive by the model provider",
                    user_id=user_id,
                    graph_exec_id=graph_exec_id,
                    moderation_type="model_provider",
                )
            raise ValueError(f"Model execution failed: {e}") from e

        if isinstance(output, list) and output:
            output = output[0]

        if isinstance(output, FileOutput):
            return MediaFileType(output.url)
        if isinstance(output, str):
            return MediaFileType(output)

        raise ValueError("No output received")