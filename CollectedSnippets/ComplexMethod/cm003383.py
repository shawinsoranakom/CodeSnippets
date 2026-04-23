def resize(
        self,
        image: torch.Tensor,
        size: SizeDict,
        size_divisor: int = 0,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None" = None,
        **kwargs,
    ) -> torch.Tensor:
        """
        Resize the image to the given size. Size can be `min_size` (scalar) or `(height, width)` tuple. If size is an
        int, smaller edge of the image will be matched to this number.

        Args:
            image (`torch.Tensor`):
                Image to resize.
            size (`SizeDict`):
                Size of the image's `(height, width)` dimensions after resizing.
            size_divisor (`int`, *optional*, defaults to 0):
                If `size_divisor` is given, the output image size will be divisible by the number.
            resample (`PILImageResampling | tvF.InterpolationMode | int | None`, *optional*):
                Resampling filter to use if resizing the image.
        """

        if size.shortest_edge and size.longest_edge:
            # Resize the image so that the shortest edge or the longest edge is of the given size
            # while maintaining the aspect ratio of the original image.
            new_size = get_size_with_aspect_ratio(
                image.size()[-2:],
                size.shortest_edge,
                size.longest_edge,
            )
        elif size.max_height and size.max_width:
            new_size = get_image_size_for_max_height_width(image.size()[-2:], size.max_height, size.max_width)
        elif size.height and size.width:
            new_size = (size.height, size.width)
        else:
            raise ValueError(
                f"Size must contain 'height' and 'width' keys or 'shortest_edge' and 'longest_edge' keys. Got {size}."
            )
        if size_divisor > 0:
            height, width = new_size
            height = int(math.ceil(height / size_divisor) * size_divisor)
            width = int(math.ceil(width / size_divisor) * size_divisor)
            new_size = (height, width)

        image = super().resize(
            image, size=SizeDict(height=new_size[0], width=new_size[1]), resample=resample, **kwargs
        )
        return image