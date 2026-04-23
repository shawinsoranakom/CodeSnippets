def _preprocess_image(
        self,
        text: list[str],
        images: list[Image.Image],
        max_num_tiles: int,
    ) -> tuple[list[str], dict[str, Any]]:
        if len(images) == 0:
            return text, {}

        image_inputs: dict[str, Any]
        if tiler := self.dynamic_tiler:
            sans_images = text[0].replace("<image>", "")
            text_prompt_length = len(
                self.tokenizer(sans_images, add_special_tokens=False).input_ids
            )
            pixel_values_lst, num_tokens_per_image = tiler._images_to_pixel_values_lst(
                text_prompt_length=text_prompt_length,
                images=images,
                dtype=self.dtype,
            )
            imgs_sizes = [(pv.shape[-2], pv.shape[-1]) for pv in pixel_values_lst]
            image_num_patches = torch.tensor([1] * len(num_tokens_per_image))
            image_inputs = {
                "pixel_values_flat": pixel_values_lst,
                "imgs_sizes": imgs_sizes,
                "num_tokens_per_image": num_tokens_per_image,
            }
        else:
            pixel_values_lst = self._images_to_pixel_values_lst(images, max_num_tiles)
            image_num_patches = torch.tensor([len(item) for item in pixel_values_lst])
            pixel_values_flat = (
                torch.cat(pixel_values_lst)
                if len(pixel_values_lst) > 1
                else pixel_values_lst[0]
            )
            image_inputs = {
                "pixel_values_flat": pixel_values_flat,
                "image_num_patches": image_num_patches,
            }
            num_tokens_per_image = [
                self.num_image_token * len(item) for item in pixel_values_lst
            ]

        assert len(text) == 1, (
            "hf_processor is called on the output of get_dummy_text, "
            "which should be a single string"
        )
        parts = [x for x in re.split(r"(<image>)", text[0]) if x]
        assert parts.count("<image>") == len(num_tokens_per_image), (
            f"Expected {len(num_tokens_per_image)} <image> tokens in text "
            f"but found {parts.count('<image>')}"
        )

        for i, (feature_size, num_patches) in enumerate(
            zip(num_tokens_per_image, image_num_patches, strict=True)
        ):
            image_repl = self.get_image_repl(feature_size, num_patches)
            parts[i] = parts[i].replace("<image>", image_repl.full)
        text = ["".join(parts)]

        return text, image_inputs