def _standardize_kwargs(
        self,
        size: int | Iterable[int] | dict[str, int] | SizeDict | None = None,
        crop_size: int | Iterable[int] | dict[str, int] | SizeDict | None = None,
        pad_size: int | Iterable[int] | dict[str, int] | SizeDict | None = None,
        default_to_square: bool | None = None,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        **kwargs,
    ) -> dict:
        """
        Standardize kwargs to canonical format before validation.
        Can be overridden by subclasses to customize the processing of kwargs.
        """
        if kwargs is None:
            kwargs = {}
        if size is not None and not isinstance(size, SizeDict):
            size = SizeDict(**get_size_dict(size=size, default_to_square=default_to_square))
        if crop_size is not None and not isinstance(crop_size, SizeDict):
            crop_size = SizeDict(**get_size_dict(crop_size, param_name="crop_size"))
        if pad_size is not None and not isinstance(pad_size, SizeDict):
            pad_size = SizeDict(**get_size_dict(size=pad_size, param_name="pad_size"))
        if isinstance(image_mean, list):
            image_mean = tuple(image_mean)
        if isinstance(image_std, list):
            image_std = tuple(image_std)

        kwargs["size"] = size
        kwargs["crop_size"] = crop_size
        kwargs["pad_size"] = pad_size
        kwargs["image_mean"] = image_mean
        kwargs["image_std"] = image_std

        return kwargs