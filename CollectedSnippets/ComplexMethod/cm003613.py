def _expand_image_tokens(
        self,
        text: list[TextInput],
        image_sizes: Iterable[list[int] | int],
        height: int,
        width: int,
        special_token: str,
        batch_num_images: Iterable[int],
    ):
        prompt_strings = []
        max_num_vision_tokens = 0
        for sample in text:
            if special_token in sample:
                num_images = next(batch_num_images)  # should consume iterable
                is_multi_image = num_images != 1
            else:
                is_multi_image = False
            while special_token in sample:
                original_size = next(image_sizes)  # should consume iterable
                if is_multi_image:
                    num_image_tokens = self.num_image_tokens + 1  # one for image_newline
                else:
                    if not isinstance(original_size, (list, tuple)):
                        # cast to list to avoid numerical precision errors when calculating unpadding
                        original_size = original_size.tolist()
                    orig_height, orig_width = original_size
                    num_image_tokens = self._get_number_of_features(orig_height, orig_width, height, width)
                max_num_vision_tokens = max(max_num_vision_tokens, num_image_tokens)
                if self.vision_feature_select_strategy == "default":
                    num_image_tokens -= 1
                sample = sample.replace(special_token, "<placeholder>" * num_image_tokens, 1)
            prompt_strings.append(sample)
        text = [sample.replace("<placeholder>", special_token) for sample in prompt_strings]
        return text, max_num_vision_tokens