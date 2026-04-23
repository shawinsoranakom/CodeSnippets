def _convert_single_sample(sample):
        """Convert a single sample to VLM format."""
        # Get image (might be PIL Image, local path, URL, or bare filename)
        image_data = sample[image_column]

        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                import fsspec
                from io import BytesIO

                with fsspec.open(image_data, "rb", expand = True) as f:
                    image_data = Image.open(BytesIO(f.read())).convert("RGB")
            elif _image_lookup is not None and image_data in _image_lookup:
                # Bare filename → resolve via HF repo lookup
                from huggingface_hub import hf_hub_download

                local_path = hf_hub_download(
                    dataset_name,
                    _image_lookup[image_data],
                    repo_type = "dataset",
                )
                image_data = Image.open(local_path).convert("RGB")
            else:
                image_data = Image.open(image_data).convert("RGB")

        # Get text (if list of strings, pick a random one — e.g. multiple captions)
        text_data = sample[text_column]
        if isinstance(text_data, list) and len(text_data) > 0:
            import random

            text_data = random.choice(text_data)

        # Get instruction (static or dynamic)
        if uses_dynamic and instruction_column:
            current_instruction = sample[instruction_column]
        else:
            current_instruction = instruction

        # Build VLM messages - simple structure
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": current_instruction},
                    {"type": "image", "image": image_data},  # PIL object
                ],
            },
            {"role": "assistant", "content": [{"type": "text", "text": text_data}]},
        ]

        # Return dict with messages
        return {"messages": messages}