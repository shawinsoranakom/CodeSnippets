def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        """Run the underlying HF processor on text and image data."""
        # Text-only input is handled as a special case here.
        if not mm_data or not mm_data.get("images", []):
            prompt_ids = self.info.get_tokenizer().encode(prompt)
            return BatchFeature(dict(input_ids=[prompt_ids]), tensor_type="pt")

        # Images
        image_inputs = mm_data.get("images", [])
        pixel_sizes = []
        if not isinstance(image_inputs[0], Image.Image):
            image_inputs = [Image.fromarray(image) for image in image_inputs]

        image_processor = self.info.get_hf_processor().image_processor
        processor_output = [image_processor(image) for image in image_inputs]
        pixel_values = [o["pixel_values"] for o in processor_output]
        image_meta = [o["image_meta"] for o in processor_output]
        # list of dict -> dict of list
        image_meta = {k: [d[k] for d in image_meta] for k in image_meta[0]}

        for pixel_value in pixel_values:
            pixel_sizes.append(pixel_value.shape[0])
        # flattened pixel_values for single example (already includes batch dim)
        pixel_values = torch.concat(pixel_values, dim=0)

        tokenizer = self.info.get_tokenizer()
        media_token = tokenizer.convert_ids_to_tokens([self.media_token_id])[0]
        prompt_replaced = prompt.replace("<image>", media_token)
        input_ids = tokenizer.encode(prompt_replaced)
        input_ids = torch.tensor(input_ids)

        # Ensure HF output is consistent with vLLM prompt-update expectations:
        # if the HF tokenizer emits exactly 1 placeholder token per image, expand
        # it to `T*H*W` placeholder tokens per image so placeholder detection works.
        num_images = len(image_inputs)
        image_token_thw = torch.tensor(image_meta["image_token_thw"])
        per_image_token_counts = image_token_thw.prod(dim=1).tolist()
        expected_total = int(sum(int(x) for x in per_image_token_counts))

        n_placeholders = int((input_ids == self.media_token_id).sum().item())
        if n_placeholders == num_images and expected_total != num_images:
            expanded: list[int] = []
            img_i = 0
            for tok in input_ids.tolist():
                if tok == self.media_token_id and img_i < num_images:
                    expanded.extend(
                        [self.media_token_id] * int(per_image_token_counts[img_i])
                    )
                    img_i += 1
                else:
                    expanded.append(tok)
            input_ids = input_ids.new_tensor(expanded)

        combined_outputs = dict(
            # Add batch dimension to input_ids.
            input_ids=input_ids.unsqueeze(0),
            pixel_values=pixel_values,
            vision_grid_thw=torch.tensor(image_meta["vision_grid_thw"]),
            image_token_thw=torch.tensor(image_meta["image_token_thw"]),
            pixel_sizes=torch.tensor(pixel_sizes),
        )
        return BatchFeature(combined_outputs, tensor_type="pt")