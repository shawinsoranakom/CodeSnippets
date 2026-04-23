def resize(
        self,
        image: "torch.Tensor",
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None" = None,
        antialias: bool = True,
        **kwargs,
    ) -> "torch.Tensor":
        """Resize an image using Torchvision."""
        # Convert PIL resample to torchvision interpolation if needed
        if resample is not None:
            if isinstance(resample, (PILImageResampling, int)):
                interpolation = pil_torch_interpolation_mapping[resample]
            else:
                interpolation = resample
        else:
            interpolation = tvF.InterpolationMode.BILINEAR
        if interpolation == tvF.InterpolationMode.LANCZOS:
            logger.warning_once(
                "You have used a torchvision backend image processor with LANCZOS resample which not yet supported for torch.Tensor. "
                "BICUBIC resample will be used as an alternative. Please fall back to a pil backend image processor if you "
                "want full consistency with the original model."
            )
            interpolation = tvF.InterpolationMode.BICUBIC

        if size.shortest_edge and size.longest_edge:
            new_size = get_size_with_aspect_ratio(
                image.size()[-2:],
                size.shortest_edge,
                size.longest_edge,
            )
        elif size.shortest_edge:
            new_size = get_resize_output_image_size(
                image,
                size=size.shortest_edge,
                default_to_square=False,
                input_data_format=ChannelDimension.FIRST,
            )
        elif size.max_height and size.max_width:
            new_size = get_image_size_for_max_height_width(image.size()[-2:], size.max_height, size.max_width)
        elif size.height and size.width:
            new_size = (size.height, size.width)
        else:
            raise ValueError(
                "Size must contain 'height' and 'width' keys, or 'max_height' and 'max_width', or 'shortest_edge' key. Got"
                f" {size}."
            )

        # Workaround for torch.compile issue with uint8 on AMD GPUs
        if is_torchdynamo_compiling() and is_rocm_platform():
            return self._compile_friendly_resize(image, new_size, interpolation, antialias)
        return tvF.resize(image, new_size, interpolation=interpolation, antialias=antialias)