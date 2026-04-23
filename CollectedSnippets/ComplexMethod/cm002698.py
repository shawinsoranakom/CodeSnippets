def resize(self, image, size, resample=None, default_to_square=True, max_size=None):
        """
        Resizes `image`. Enforces conversion of input to PIL.Image.

        Args:
            image (`PIL.Image.Image` or `np.ndarray` or `torch.Tensor`):
                The image to resize.
            size (`int` or `tuple[int, int]`):
                The size to use for resizing the image. If `size` is a sequence like (h, w), output size will be
                matched to this.

                If `size` is an int and `default_to_square` is `True`, then image will be resized to (size, size). If
                `size` is an int and `default_to_square` is `False`, then smaller edge of the image will be matched to
                this number. i.e, if height > width, then image will be rescaled to (size * height / width, size).
            resample (`int`, *optional*, defaults to `PILImageResampling.BILINEAR`):
                The filter to user for resampling.
            default_to_square (`bool`, *optional*, defaults to `True`):
                How to convert `size` when it is a single int. If set to `True`, the `size` will be converted to a
                square (`size`,`size`). If set to `False`, will replicate
                [`torchvision.transforms.Resize`](https://pytorch.org/vision/stable/transforms.html#torchvision.transforms.Resize)
                with support for resizing only the smallest edge and providing an optional `max_size`.
            max_size (`int`, *optional*, defaults to `None`):
                The maximum allowed for the longer edge of the resized image: if the longer edge of the image is
                greater than `max_size` after being resized according to `size`, then the image is resized again so
                that the longer edge is equal to `max_size`. As a result, `size` might be overruled, i.e the smaller
                edge may be shorter than `size`. Only used if `default_to_square` is `False`.

        Returns:
            image: A resized `PIL.Image.Image`.
        """
        resample = resample if resample is not None else PILImageResampling.BILINEAR

        self._ensure_format_supported(image)

        if not isinstance(image, PIL.Image.Image):
            image = self.to_pil_image(image)

        if isinstance(size, list):
            size = tuple(size)

        if isinstance(size, int) or len(size) == 1:
            if default_to_square:
                size = (size, size) if isinstance(size, int) else (size[0], size[0])
            else:
                width, height = image.size
                # specified size only for the smallest edge
                short, long = (width, height) if width <= height else (height, width)
                requested_new_short = size if isinstance(size, int) else size[0]

                if short == requested_new_short:
                    return image

                new_short, new_long = requested_new_short, int(requested_new_short * long / short)

                if max_size is not None:
                    if max_size <= requested_new_short:
                        raise ValueError(
                            f"max_size = {max_size} must be strictly greater than the requested "
                            f"size for the smaller edge size = {size}"
                        )
                    if new_long > max_size:
                        new_short, new_long = int(max_size * new_short / new_long), max_size

                size = (new_short, new_long) if width <= height else (new_long, new_short)

        return image.resize(size, resample=resample)