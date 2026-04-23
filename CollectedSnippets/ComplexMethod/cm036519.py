def patched_get_inputs(prompts, images=None, videos=None, audios=None, **kwargs):
        all_inputs = []
        for i, prompt in enumerate(prompts):
            content: list[dict] = []

            if audios is not None and audios[i] is not None:
                items = audios[i]
                if not isinstance(items, list):
                    items = [items]
                for item in items:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        arr, sr = item
                    else:
                        arr, sr = item, 16_000
                    content.append(
                        {
                            "type": "audio",
                            "base64": _audio_to_base64(arr, sr),
                        }
                    )

            content.append({"type": "text", "text": prompt})

            inputs = processor.apply_chat_template(
                [{"role": "user", "content": content}]
            )
            if hasattr(inputs, "to"):
                inputs = inputs.to(dtype=hf_model.dtype)
            all_inputs.append(inputs)

        return all_inputs