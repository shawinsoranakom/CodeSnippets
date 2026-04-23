def _verify_np_shape(array: "npt.NDArray[Any]") -> "npt.NDArray[Any]":
    if len(array.shape) not in (2, 3):
        raise StreamlitAPIException("Numpy shape has to be of length 2 or 3.")
    if len(array.shape) == 3 and array.shape[-1] not in (1, 3, 4):
        raise StreamlitAPIException(
            "Channel can only be 1, 3, or 4 got %d. Shape is %s"
            % (array.shape[-1], str(array.shape))
        )

    # If there's only one channel, convert is to x, y
    if len(array.shape) == 3 and array.shape[-1] == 1:
        array = array[:, :, 0]

    return array