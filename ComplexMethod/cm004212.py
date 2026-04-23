def __call__(
        self,
        images: ImageInput | list[ImageInput] | str | list[str] | list[list[str]] = None,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput]
        | list[list[TextInput]]
        | list[list[PreTokenizedInput]] = None,
        **kwargs: Unpack[IdeficsProcessorKwargs],
    ) -> BatchFeature:
        r"""
        Returns:
            a dict with entries: `input_ids`, `attention_mask`, `pixel_values`, `image_attention_mask` which can be
            directly passed to `model.generate`

            Detailed explanation:

            Each entry in `text` is either a text to be passed as is or an image that will be processed.

            An image can be either an image object (`PIL.Image`) or a url from which the image can be retrieved.

        When the processor encounters an image it'll inject `<fake_token_around_image><image><fake_token_around_image>`
        entry into the prompt.

        Example:

        ```python
        checkpoint = "HuggingFaceM4/idefics-9b"
        processor = AutoProcessor.from_pretrained(checkpoint)
        url = "https://hips.hearstapps.com/hmg-prod/images/cute-photos-of-cats-in-grass-1593184777.jpg"
        img = processor.image_processor.fetch_images([url])[0]

        prompts = [
            "User:",
            img,
            "Describe this image.\nAssistant: An image of two kittens in grass.\n",
            "User:",
            "https://hips.hearstapps.com/hmg-prod/images/dog-puns-1581708208.jpg",
            "Describe this image.\nAssistant:",
        ]

        inputs = processor(text=prompts, return_tensors="pt")
        generated_ids = model.generate(**inputs, max_length=100)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        ```

        In this example the `prompts` will be converted into:

        ```
        <s>User:<fake_token_around_image><image><fake_token_around_image>Describe this image.
        Assistant: An image of two kittens in grass.
        User:<fake_token_around_image><image><fake_token_around_image>Describe this image.
        Assistant:'
        ```

        and the two images will be massaged using [`IdeficsImageProcessor.__call__`] method and placed inside the
        `pixel_values` dict entry of the return value.

        This example also exemplifies that images can be passed as objects or as text urls. It can be seen that the
        first image is passed as object and the second one as a url.

        To do training do:

        ```python
        image_transform = transforms.Compose(
            [
                transforms.RandomResizedCrop(
                    (w, h), scale=(0.9, 1.0), interpolation=transforms.InterpolationMode.BICUBIC
                ),
                transforms.ToTensor(),
                transforms.Normalize(mean=self.image_mean, std=self.image_std),
            ]
        )
        inputs = processor(text=prompts, transform=image_transform, return_tensors="pt")
        ```

        In order to help debug prompt generation enable `debug=True` which will show you what's happening.

        """
        if images is None and text is None:
            raise ValueError("You need to specify either `text` or `images` and `text`.")

        if images is None:
            # assuming the user wants to use the old behavior with prompts as the only argument
            prompts = text
        elif text is not None:
            # Assuming image-text-to-text behavior:
            # Check if batched images are provided
            if not isinstance(images, (list, tuple)):
                images = [images]
            if isinstance(text, str):
                text = [text]
            # Check if batched images and text are in the correct format
            if isinstance(text, (list, tuple)) and len(text) != len(images):
                raise ValueError(
                    "When providing both images and text arguments, the number of text prompts should be the same as the number of images."
                    "If you want to have several images per prompt, images should be nested as such: images=[[img1, img2], [img3, img4], ...] for text=[prompt1, prompt2, ...]."
                )
            # Check that only text is present in the prompts
            if not all(isinstance(i, str) for i in text):
                raise ValueError("When using the image-text-to-text behavior, the prompts should only contain text.")
            if isinstance(images[0], (list, tuple)):
                # if nested images, un-nest each sublist and create `prompts`
                prompts = [[sample, *image_list] for image_list, sample in zip(images, text)]
            else:
                prompts = list(zip(images, text))

        output_kwargs = self._merge_kwargs(
            IdeficsProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        add_eos_token = output_kwargs["text_kwargs"].pop("add_eos_token", False)
        add_end_of_utterance_token = output_kwargs["text_kwargs"].pop("add_end_of_utterance_token", None)

        # if the value isn't overridden by the user, check if the tokenizer was trained with this token and then use it
        if add_end_of_utterance_token is None:
            add_end_of_utterance_token = self.tokenizer_was_trained_with_end_of_utterance_token
        # turn non-batched prompts into batched
        if not any(isinstance(i, (list, tuple)) for i in prompts):
            prompts = [prompts]

        fake_token = "<fake_token_around_image>"
        image_token = "<image>"
        end_of_utterance_token = "<end_of_utterance>"

        def image_tokens(last_was_image):
            if last_was_image:
                return image_token + fake_token
            else:
                return fake_token + image_token + fake_token

        all_prompts = []
        all_images = []
        for sample in prompts:
            # the model was trained on samples starting with <s>
            full_text = f"{self.tokenizer.bos_token}"

            # an image can either be an image object in the item or the url, everything else is a verbatim prompt text
            image_objects = []
            last_was_image = False
            last_was_text = False
            for i, item in enumerate(sample):
                if i > 0:
                    last_was_text = bool(not last_was_image)

                if isinstance(item, str):
                    item = item.strip(" ")
                    if is_url(item):
                        image = self.image_processor.fetch_images(item)
                        full_text += image_tokens(last_was_image)
                        image_objects.append(image)
                        last_was_image = True
                    else:
                        # we add end_of_utterance_token between each subsequent text prompts (but not at the last one!)
                        if add_end_of_utterance_token and last_was_text:
                            full_text += end_of_utterance_token
                        full_text += item
                        last_was_image = False
                else:
                    # must be an image obj
                    full_text += image_tokens(last_was_image)
                    image_objects.append(item)
                    last_was_image = True

            if add_eos_token:
                full_text += self.tokenizer.eos_token

            if len(image_objects) > 0:
                image_objects = self.image_processor(image_objects, **output_kwargs["images_kwargs"])

            all_prompts.append(full_text)
            all_images.append(image_objects)

        # For BC
        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", "pt")
        text_encoding = self.tokenizer(all_prompts, **output_kwargs["text_kwargs"])
        all_texts = text_encoding["input_ids"]
        all_attention_masks = text_encoding["attention_mask"]

        # max_num_images has to be at least 1 even when there are no images
        max_num_images = max(len(x) for x in all_images)
        max_num_images = max(1, max_num_images)

        at_least_one_image = sum(len(x) for x in all_images) > 0
        output_input_ids = []
        output_images = []
        output_attention_masks = []

        for text_single, attention_mask, extracted_images in zip(all_texts, all_attention_masks, all_images):
            padded_input_ids = text_single
            image_count = padded_input_ids.count(self.image_token_id)
            local_max_num_images = min(image_count, max_num_images)
            current_images = extracted_images[:local_max_num_images]

            if len(current_images) > 0:
                if return_tensors == "pt":
                    padded_image_tensor = torch.zeros(max_num_images, *current_images.size()[1:])
                    padded_image_tensor[: current_images.size(0)] = current_images
            else:
                if return_tensors == "pt":
                    padded_image_tensor = torch.zeros(max_num_images, *self.default_image_dims)

            output_images.append(padded_image_tensor)
            if return_tensors == "pt":
                output_input_ids.append(torch.tensor(padded_input_ids))
                output_attention_masks.append(torch.tensor(attention_mask))

        if return_tensors == "pt":
            output_input_ids = torch.stack(output_input_ids)
            output_images = torch.stack(output_images)
            output_attention_masks = torch.stack(output_attention_masks)

        if at_least_one_image:
            image_attention_mask, _ = image_attention_mask_for_packed_input_ids(
                output_input_ids, self.tokenizer, return_tensors
            )
            image_attention_mask = incremental_to_binary_attention_mask(
                image_attention_mask, return_tensors, num_classes=max_num_images
            )
        else:
            # in full language mode we set the image mask to all-0s
            if return_tensors == "pt":
                image_attention_mask = torch.zeros(
                    output_input_ids.shape[0], output_input_ids.shape[1], 1, dtype=torch.bool
                )
        return BatchFeature(
            data={
                "input_ids": output_input_ids,
                "attention_mask": output_attention_masks,
                "pixel_values": output_images,
                "image_attention_mask": image_attention_mask,
            }
        )