def _clip_image(image: "npt.NDArray[Any]", clamp: bool) -> "npt.NDArray[Any]":
    data = image
    if issubclass(image.dtype.type, np.floating):
        if clamp:
            data = np.clip(image, 0, 1.0)
        else:
            if np.amin(image) < 0.0 or np.amax(image) > 1.0:
                raise RuntimeError("Data is outside [0.0, 1.0] and clamp is not set.")
        data = data * 255
    else:
        if clamp:
            data = np.clip(image, 0, 255)
        else:
            if np.amin(image) < 0 or np.amax(image) > 255:
                raise RuntimeError("Data is outside [0, 255] and clamp is not set.")
    return data