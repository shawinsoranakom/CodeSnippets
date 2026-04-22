def _4d_to_list_3d(array: "npt.NDArray[Any]") -> List["npt.NDArray[Any]"]:
    return [array[i, :, :, :] for i in range(0, array.shape[0])]