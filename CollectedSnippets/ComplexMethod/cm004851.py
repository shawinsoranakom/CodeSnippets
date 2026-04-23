def _standardize_kwargs(
        self,
        size: int | Iterable[int] | dict[str, int] | SizeDict | None = None,
        high_res_size: int | Iterable[int] | dict[str, int] | SizeDict | None = None,
        default_to_square: bool | None = None,
        image_mean: float | list[float] | None = None,
        image_std: float | list[float] | None = None,
        high_res_image_mean: float | list[float] | None = None,
        high_res_image_std: float | list[float] | None = None,
        **kwargs,
    ) -> dict:
        """
        Update kwargs that need further processing before being validated
        Can be overridden by subclasses to customize the processing of kwargs.
        """
        if kwargs is None:
            kwargs = {}
        if size is not None and not isinstance(size, SizeDict):
            size = SizeDict(**get_size_dict(size=size, default_to_square=default_to_square))
        if high_res_size is not None and not isinstance(high_res_size, SizeDict):
            high_res_size = SizeDict(**get_size_dict(size=high_res_size, default_to_square=default_to_square))
        if isinstance(image_mean, list):
            image_mean = tuple(image_mean)
        if isinstance(image_std, list):
            image_std = tuple(image_std)
        if isinstance(high_res_image_mean, list):
            high_res_image_mean = tuple(high_res_image_mean)
        if isinstance(high_res_image_std, list):
            high_res_image_std = tuple(high_res_image_std)

        kwargs["size"] = size
        kwargs["high_res_size"] = high_res_size
        kwargs["image_mean"] = image_mean
        kwargs["image_std"] = image_std
        kwargs["high_res_image_mean"] = high_res_image_mean
        kwargs["high_res_image_std"] = high_res_image_std

        return kwargs