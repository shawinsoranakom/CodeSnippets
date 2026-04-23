def _get_num_multimodal_tokens(self, image_sizes=None, audio_lengths=None, **kwargs):
        """
        Computes the number of placeholder tokens needed for multimodal inputs with the given sizes.

        Args:
            image_sizes (`list[list[int]]`, *optional*):
                The input sizes formatted as (height, width) per each image.
            audio_lengths (`list[int]`, *optional*):
                The lengths of audio inputs in number of samples. Used to dynamically
                compute per-audio token counts.

        Returns:
            `MultiModalData`: A `MultiModalData` object holding number of tokens per each of the provided
            input modalities, along with other useful data.
        """

        images_kwargs = Gemma4ProcessorKwargs._defaults.get("images_kwargs", {})
        images_kwargs.update(kwargs)
        patch_size = images_kwargs.get("patch_size", None) or self.image_processor.patch_size
        pooling_kernel_size = (
            images_kwargs.get("pooling_kernel_size", None) or self.image_processor.pooling_kernel_size
        )
        max_soft_tokens = images_kwargs.get("max_soft_tokens", None) or self.image_processor.max_soft_tokens

        max_patches = max_soft_tokens * pooling_kernel_size**2

        vision_data = {}
        if image_sizes is not None:
            num_image_tokens = []
            for image_size in image_sizes:
                target_h, target_w = get_aspect_ratio_preserving_size(
                    height=image_size[0],
                    width=image_size[1],
                    patch_size=patch_size,
                    max_patches=max_patches,
                    pooling_kernel_size=pooling_kernel_size,
                )
                patch_height = target_h // patch_size
                patch_width = target_w // patch_size
                num_image_tokens.append(patch_height * patch_width // pooling_kernel_size**2)

            num_image_patches = [1] * len(image_sizes)
            vision_data.update({"num_image_tokens": num_image_tokens, "num_image_patches": num_image_patches})

        if audio_lengths is not None:
            # Dynamically compute per-audio token counts from sample lengths.
            # audio_lengths are in number of samples; assume default sampling rate.
            sampling_rate = getattr(self.feature_extractor, "sampling_rate", 16_000)
            num_audio_tokens = [
                self._compute_audio_num_tokens(np.zeros(length), sampling_rate) for length in audio_lengths
            ]
            vision_data.update({"num_audio_tokens": num_audio_tokens})

        return MultiModalData(**vision_data)