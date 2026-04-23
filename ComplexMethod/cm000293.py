def similarity_search(
    dataset: np.ndarray, value_array: np.ndarray
) -> list[list[list[float] | float]]:
    """
    :param dataset: Set containing the vectors. Should be ndarray.
    :param value_array: vector/vectors we want to know the nearest vector from dataset.
    :return: Result will be a list containing
            1. the nearest vector
            2. distance from the vector

    >>> dataset = np.array([[0], [1], [2]])
    >>> value_array = np.array([[0]])
    >>> similarity_search(dataset, value_array)
    [[[0], 0.0]]

    >>> dataset = np.array([[0, 0], [1, 1], [2, 2]])
    >>> value_array = np.array([[0, 1]])
    >>> similarity_search(dataset, value_array)
    [[[0, 0], 1.0]]

    >>> dataset = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
    >>> value_array = np.array([[0, 0, 1]])
    >>> similarity_search(dataset, value_array)
    [[[0, 0, 0], 1.0]]

    >>> dataset = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
    >>> value_array = np.array([[0, 0, 0], [0, 0, 1]])
    >>> similarity_search(dataset, value_array)
    [[[0, 0, 0], 0.0], [[0, 0, 0], 1.0]]

    These are the errors that might occur:

    1. If dimensions are different.
    For example, dataset has 2d array and value_array has 1d array:
    >>> dataset = np.array([[1]])
    >>> value_array = np.array([1])
    >>> similarity_search(dataset, value_array)
    Traceback (most recent call last):
        ...
    ValueError: Wrong input data's dimensions... dataset : 2, value_array : 1

    2. If data's shapes are different.
    For example, dataset has shape of (3, 2) and value_array has (2, 3).
    We are expecting same shapes of two arrays, so it is wrong.
    >>> dataset = np.array([[0, 0], [1, 1], [2, 2]])
    >>> value_array = np.array([[0, 0, 0], [0, 0, 1]])
    >>> similarity_search(dataset, value_array)
    Traceback (most recent call last):
        ...
    ValueError: Wrong input data's shape... dataset : 2, value_array : 3

    3. If data types are different.
    When trying to compare, we are expecting same types so they should be same.
    If not, it'll come up with errors.
    >>> dataset = np.array([[0, 0], [1, 1], [2, 2]], dtype=np.float32)
    >>> value_array = np.array([[0, 0], [0, 1]], dtype=np.int32)
    >>> similarity_search(dataset, value_array)  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    TypeError: Input data have different datatype...
    dataset : float32, value_array : int32
    """

    if dataset.ndim != value_array.ndim:
        msg = (
            "Wrong input data's dimensions... "
            f"dataset : {dataset.ndim}, value_array : {value_array.ndim}"
        )
        raise ValueError(msg)

    try:
        if dataset.shape[1] != value_array.shape[1]:
            msg = (
                "Wrong input data's shape... "
                f"dataset : {dataset.shape[1]}, value_array : {value_array.shape[1]}"
            )
            raise ValueError(msg)
    except IndexError:
        if dataset.ndim != value_array.ndim:
            raise TypeError("Wrong shape")

    if dataset.dtype != value_array.dtype:
        msg = (
            "Input data have different datatype... "
            f"dataset : {dataset.dtype}, value_array : {value_array.dtype}"
        )
        raise TypeError(msg)

    answer = []

    for value in value_array:
        dist = euclidean(value, dataset[0])
        vector = dataset[0].tolist()

        for dataset_value in dataset[1:]:
            temp_dist = euclidean(value, dataset_value)

            if dist > temp_dist:
                dist = temp_dist
                vector = dataset_value.tolist()

        answer.append([vector, dist])

    return answer