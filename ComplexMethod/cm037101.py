def __call__(
        self,
        text: str | list[str] | None = None,
        images: Image.Image | list[Image.Image] | None = None,
        videos: npt.NDArray | list[npt.NDArray] | None = None,
        *,
        min_dynamic_patch: int | None = None,
        max_dynamic_patch: int | None = None,
        dynamic_image_size: bool | None = None,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchFeature:
        if images is not None:
            image_inputs = self.image_processor(
                images=images,
                min_dynamic_patch=min_dynamic_patch,
                max_dynamic_patch=max_dynamic_patch,
                dynamic_image_size=dynamic_image_size,
                return_tensors=return_tensors,
            )
            image_num_patches = image_inputs["image_num_patches"]
        else:
            image_inputs = {}
            image_num_patches = []

        if videos is not None:
            if self.video_processor is None:
                raise ValueError("This model does not support video inputs")

            video_inputs = self.video_processor(
                videos=videos,
                return_tensors=return_tensors,
            )
            video_num_patches = video_inputs["video_num_patches"]
        else:
            video_inputs = {}
            video_num_patches = []

        if text is not None:
            if not isinstance(text, list):
                text = [text]

            if image_inputs:
                image_token = "<image>"
                image_index = 0
                processed_text = list[str]()
                replace_strings = list[str]()

                for prompt in text:
                    new_prompt = prompt

                    while image_token in new_prompt:
                        new_prompt = new_prompt.replace(image_token, "<placeholder>", 1)
                        image_repl = self.get_image_repl(image_num_patches[image_index])
                        replace_strings.append(image_repl.full)
                        image_index += 1

                    while "<placeholder>" in new_prompt:
                        replace_str = replace_strings.pop(0)
                        new_prompt = new_prompt.replace("<placeholder>", replace_str, 1)

                    processed_text.append(new_prompt)

                text = processed_text

            if video_inputs:
                video_token = "<video>"
                video_index = 0
                processed_text = list[str]()
                replace_strings = list[str]()

                assert video_token is not None

                for prompt in text:
                    new_prompt = prompt

                    while video_token in new_prompt:
                        new_prompt = new_prompt.replace(video_token, "<placeholder>", 1)
                        video_repl = self.get_video_repl(video_num_patches[video_index])
                        replace_strings.append(video_repl.full)
                        video_index += 1

                    while "<placeholder>" in new_prompt:
                        replace_str = replace_strings.pop(0)
                        new_prompt = new_prompt.replace("<placeholder>", replace_str, 1)

                    processed_text.append(new_prompt)

                text = processed_text

            text_inputs = self.tokenizer(text, return_tensors=return_tensors)
        else:
            text_inputs = {}

        return BatchFeature(
            data={**text_inputs, **image_inputs, **video_inputs},
            tensor_type=return_tensors,
        )