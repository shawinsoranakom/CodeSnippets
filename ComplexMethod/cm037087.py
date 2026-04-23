def __init__(
        self,
        do_resize: bool = True,
        size: dict[str, int] | None = None,
        resample: PILImageResampling = PILImageResampling.BICUBIC,
        do_rescale: bool = True,
        rescale_factor: int | float = 1 / 255,
        do_normalize: bool = True,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        do_convert_rgb: bool = True,
        min_pixels: int | None = None,
        max_pixels: int | None = None,
        patch_size: int = 16,
        temporal_patch_size: int = 2,
        merge_size: int = 2,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if size is not None and (
            "shortest_edge" not in size or "longest_edge" not in size
        ):
            raise ValueError(
                "size must contain 'shortest_edge' and 'longest_edge' keys."
            )
        else:
            size = {"shortest_edge": 512 * 512, "longest_edge": 2048 * 2048}
        # backward compatibility: override size with min_pixels and max_pixels
        # if they are provided.
        if min_pixels is not None:
            size["shortest_edge"] = min_pixels
        if max_pixels is not None:
            size["longest_edge"] = max_pixels
        self.min_pixels = size["shortest_edge"]
        self.max_pixels = size["longest_edge"]
        self.size = size

        self.do_resize = do_resize
        self.resample = resample
        self.do_rescale = do_rescale
        self.rescale_factor = rescale_factor
        self.do_normalize = do_normalize
        self.image_mean = image_mean if image_mean is not None else OPENAI_CLIP_MEAN
        self.image_std = image_std if image_std is not None else OPENAI_CLIP_STD

        self.patch_size = patch_size
        self.temporal_patch_size = temporal_patch_size
        self.merge_size = merge_size
        self.do_convert_rgb = do_convert_rgb