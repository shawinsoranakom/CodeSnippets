def __call__(
        self,
        images: ImageInput | list[ImageInput] | list[list[ImageInput]] = None,
        text: Union[TextInput, "PreTokenizedInput", list[TextInput], list["PreTokenizedInput"]] = None,
        **kwargs: Unpack[Idefics2ProcessorKwargs],
    ) -> BatchFeature:
        if text is None and images is None:
            raise ValueError("You must provide either `text` or `images`.")

        output_kwargs = self._merge_kwargs(
            Idefics2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)

        n_images_in_text = []
        inputs = {}

        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not isinstance(text, list) and not isinstance(text[0], str):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")

            # Replace the image token with fake tokens around the expanded image token sequence of length `image_seq_len`
            fake_image_token = self.fake_image_token
            image_token = self.image_token
            image_str = f"{fake_image_token}{image_token * self.image_seq_len}{fake_image_token}"

            if self.image_processor.do_image_splitting:
                # A single image token is split into 4 patches + 1 original image
                image_str = image_str * 5

            prompt_strings = []
            closing_fake_pattern = re.compile(rf"{re.escape(fake_image_token)}(?=[^\s<])")
            for sample in text:
                n_images_in_text.append(sample.count(image_token))
                sample = sample.replace(image_token, image_str)
                # Remove any double fake tokens if images are adjacent
                sample = sample.replace(f"{fake_image_token}{fake_image_token}", f"{fake_image_token}")
                # Ensure words attached directly after the closing fake token remain word-boundary aligned
                sample = closing_fake_pattern.sub(f"{fake_image_token} ", sample)
                prompt_strings.append(sample)

            text_inputs = self.tokenizer(prompt_strings, **output_kwargs["text_kwargs"])
            self._check_special_mm_tokens(prompt_strings, text_inputs, modalities=["image"])
            inputs.update(text_inputs)

        if images is not None:
            if is_image_or_image_url(images):
                images = [[images]]
            elif isinstance(images, (list, tuple)) and is_image_or_image_url(images[0]):
                if text is not None:
                    if sum(n_images_in_text) != len(images):
                        raise ValueError(
                            f"The total number of {image_token} tokens in the prompts should be the same as the number of images passed."
                            f" Found {sum(n_images_in_text)} {image_token} tokens and {len(images)} images."
                        )
                    # Reorganize the images to match the prompts
                    cumsum_images_in_text = [0] + list(accumulate(n_images_in_text))
                    images = [
                        images[cumsum_images_in_text[i] : cumsum_images_in_text[i + 1]]
                        for i in range(len(n_images_in_text))
                    ]
                else:
                    images = [images]

            elif (
                not isinstance(images, (list, tuple))
                and not isinstance(images[0], (list, tuple))
                and not is_image_or_image_url(images[0][0])
            ):
                raise ValueError(
                    "Invalid input images. Please provide a single image or a list of images or a list of list of images."
                )

            n_images_in_images = [len(sample) for sample in images]
            if text is not None and not n_images_in_images == n_images_in_text:
                raise ValueError(
                    f"The number of images in the text {n_images_in_text} and images  {n_images_in_images} should be the same."
                )

            # Load images if they are URLs
            images = [[load_image(im) for im in sample] for sample in images]
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])
            inputs.update(image_inputs)

        return BatchFeature(inputs, tensor_type=return_tensors)