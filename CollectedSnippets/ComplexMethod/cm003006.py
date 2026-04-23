def process_images(
        self,
        images: ImageInput | None = None,
        **kwargs: Unpack[ColModernVBertProcessorKwargs],
    ) -> BatchFeature:
        """
        Prepare for the model one or several image(s). Handles input validation, RGB conversion,
        and prepends the `visual_prompt_prefix` to each image. Optionally computes labels from
        `token_type_ids` when a `suffix` is provided in `text_kwargs`.

        Args:
            images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`, `list[PIL.Image.Image]`, `list[np.ndarray]`, `list[torch.Tensor]`):
                The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                tensor. In case of a NumPy array/PyTorch tensor, each image should be of shape (C, H, W), where C is a
                number of channels, H and W are image height and width.
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors of a particular framework. Acceptable values are:

                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return NumPy `np.ndarray` objects.

        Returns:
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """
        output_kwargs = self._merge_kwargs(
            ColModernVBertProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        suffix = output_kwargs["text_kwargs"].pop("suffix", None)

        return_token_type_ids = suffix is not None

        # Normalize input to a flat list of images
        if is_valid_image(images):
            images = [images]
        elif isinstance(images, list) and is_valid_image(images[0]):
            pass
        elif not (isinstance(images, list) and isinstance(images[0], list) and is_valid_image(images[0][0])):
            raise ValueError("images must be an image, list of images or list of list of images")

        # Ensure all images are in RGB format
        images = [image.convert("RGB") for image in images]

        # Pair each image with the visual prompt prefix for the VLM backbone
        batch_doc = self.__call__(
            text=[self.visual_prompt_prefix] * len(images),
            images=images,
            images_kwargs=output_kwargs["images_kwargs"],
            text_kwargs=output_kwargs["text_kwargs"],
        )

        # When suffix is provided, generate labels by masking non-suffix tokens
        if return_token_type_ids:
            labels = batch_doc["input_ids"].masked_fill(batch_doc["token_type_ids"] == 0, -100)
            batch_doc.update({"labels": labels})

        return batch_doc