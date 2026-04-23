def _resize_data(
    _data: Image.Image | np.ndarray, size_factor: float
) -> Image.Image | np.ndarray:
    assert size_factor <= 1, "Size factor must be less than 1"
    # Image input
    if isinstance(_data, Image.Image):
        W, H = _data.width, _data.height
        W, H = map(lambda x: int(x * size_factor), (W, H))
        return _data.resize((W, H))
    # Video input with PIL Images
    elif is_list_of(_data, Image.Image):
        W, H = next(iter(_data)).width, next(iter(_data)).height
        T = len(_data)
        T, W, H = map(lambda x: max(int(x * size_factor), 2), (T, W, H))
        return [d.resize((W, H)) for d in _data[:T]]
    # Video input with numpy arrays
    elif isinstance(_data, np.ndarray) and _data.ndim >= 4:
        T, H, W, C = _data.shape[-4:]
        T, H, W = map(lambda x: max(int(x * size_factor), 2), (T, H, W))
        return _data[..., :T, :H, :W, :C]
    # Audio input
    elif isinstance(_data, np.ndarray) and _data.ndim == 1:
        return _data[: int(len(_data) * size_factor)]
    raise AssertionError("This line should be unreachable.")