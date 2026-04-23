def resize(
        self,
        image: np.ndarray,
        size: SizeDict,
        resample: "PILImageResampling | None" = None,
        reducing_gap: int | None = None,
        **kwargs,
    ) -> np.ndarray:
        """Resize an image using PIL/NumPy."""
        # PIL backend only supports PILImageResampling
        if resample is not None and not isinstance(resample, (PILImageResampling, int)):
            if torch_pil_interpolation_mapping is not None and resample in torch_pil_interpolation_mapping:
                resample = torch_pil_interpolation_mapping[resample]
            else:
                resample = PILImageResampling.BILINEAR
        resample = resample if resample is not None else PILImageResampling.BILINEAR

        if size.shortest_edge and size.longest_edge:
            height, width = get_image_size(image, channel_dim=ChannelDimension.FIRST)
            new_size = get_size_with_aspect_ratio(
                (height, width),
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
            height, width = get_image_size(image, channel_dim=ChannelDimension.FIRST)
            new_size = get_image_size_for_max_height_width((height, width), size.max_height, size.max_width)
        elif size.height and size.width:
            new_size = (size.height, size.width)
        else:
            raise ValueError(
                "Size must contain 'height' and 'width' keys, or 'max_height' and 'max_width', or 'shortest_edge' key. Got"
                f" {size}."
            )

        return np_resize(
            image,
            size=new_size,
            resample=resample,
            reducing_gap=reducing_gap,
            data_format=ChannelDimension.FIRST,
            input_data_format=ChannelDimension.FIRST,
        )