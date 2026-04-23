def bucket_sort(my_list: list, bucket_count: int = 10) -> list:
    """
    >>> data = [-1, 2, -5, 0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [9, 8, 7, 6, -12]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [.4, 1.2, .1, .2, -.9]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> bucket_sort([]) == sorted([])
    True
    >>> data = [-1e10, 1e10]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> import random
    >>> collection = random.sample(range(-50, 50), 50)
    >>> bucket_sort(collection) == sorted(collection)
    True
    >>> data = [1, 2, 2, 1, 1, 3]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [5, 5, 5, 5, 5]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [1000, -1000, 500, -500, 0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [5.5, 2.2, -1.1, 3.3, 0.0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> bucket_sort([1]) == [1]
    True
    >>> data = [-1.1, -1.5, -3.4, 2.5, 3.6, -3.3]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [9, 2, 7, 1, 5]
    >>> bucket_sort(data) == sorted(data)
    True
    """

    if len(my_list) == 0 or bucket_count <= 0:
        return []

    min_value, max_value = min(my_list), max(my_list)
    if min_value == max_value:
        return my_list

    bucket_size = (max_value - min_value) / bucket_count
    buckets: list[list] = [[] for _ in range(bucket_count)]

    for val in my_list:
        index = min(int((val - min_value) / bucket_size), bucket_count - 1)
        buckets[index].append(val)

    return [val for bucket in buckets for val in sorted(bucket)]