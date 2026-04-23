def avgpooling(arr: np.ndarray, size: int, stride: int) -> np.ndarray:

    arr = np.array(arr)
    if arr.shape[0] != arr.shape[1]:
        raise ValueError("The input array is not a square matrix")
    i = 0
    j = 0
    mat_i = 0
    mat_j = 0

    avgpool_shape = (arr.shape[0] - size) // stride + 1
    updated_arr = np.zeros((avgpool_shape, avgpool_shape))

    while i < arr.shape[0]:
        if i + size > arr.shape[0]:
            break
        while j < arr.shape[1]:
            if j + size > arr.shape[1]:
                break
            updated_arr[mat_i][mat_j] = int(np.average(arr[i : i + size, j : j + size]))
            j += stride
            mat_j += 1

        i += stride
        mat_i += 1
        j = 0
        mat_j = 0

    return updated_arr
