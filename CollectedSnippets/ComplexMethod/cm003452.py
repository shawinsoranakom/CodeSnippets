def resize(
        self,
        image: np.ndarray,
        size: SizeDict,
        resample: Optional["PILImageResampling"] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        Resize the image to the given size. Size can be `min_size` (scalar) or `(height, width)` tuple. If size is an
        int, smaller edge of the image will be matched to this number.

        Args:
            image (`np.ndarray`):
                Image to resize.
            size (`SizeDict`):
                Size of the image's `(height, width)` dimensions after resizing. Available options are:
                    - `{"height": int, "width": int}`: The image will be resized to the exact size `(height, width)`.
                        Do NOT keep the aspect ratio.
                    - `{"shortest_edge": int, "longest_edge": int}`: The image will be resized to a maximum size respecting
                        the aspect ratio and keeping the shortest edge less or equal to `shortest_edge` and the longest edge
                        less or equal to `longest_edge`.
                    - `{"max_height": int, "max_width": int}`: The image will be resized to the maximum size respecting the
                        aspect ratio and keeping the height less or equal to `max_height` and the width less or equal to
                        `max_width`.
            resample (`PILImageResampling`, *optional*, defaults to `PILImageResampling.BILINEAR`):
                Resampling filter to use if resizing the image.
        """
        resample = resample if resample is not None else self.resample

        if size.shortest_edge and size.longest_edge:
            # Resize the image so that the shortest edge or the longest edge is of the given size
            # while maintaining the aspect ratio of the original image.
            new_size = get_size_with_aspect_ratio_yolos(
                image.shape[-2:],
                size.shortest_edge,
                size.longest_edge or size.shortest_edge,
            )
        elif size.max_height and size.max_width:
            new_size = get_image_size_for_max_height_width(image.shape[-2:], size.max_height, size.max_width)
        elif size.height and size.width:
            new_size = (size.height, size.width)
        else:
            raise ValueError(
                f"Size must contain 'height' and 'width' keys or 'shortest_edge' and 'longest_edge' keys. Got {size}."
            )

        image = super().resize(
            image,
            size=SizeDict(height=new_size[0], width=new_size[1]),
            resample=resample,
            **kwargs,
        )
        return image