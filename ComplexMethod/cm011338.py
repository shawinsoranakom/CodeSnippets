def _split_by_size_and_type(bins: int, items: list[WriteItem]) -> list[list[WriteItem]]:
    if bins == 1:
        return [items]

    bytes_w = [wi for wi in items if wi.type == WriteItemType.BYTE_IO]
    tensor_w = [wi for wi in items if wi.type != WriteItemType.BYTE_IO]

    buckets: list[list[WriteItem]] = [[] for _ in range(bins)]
    bucket_sizes = [0 for _ in range(bins)]

    tensor_w.sort(key=_item_size, reverse=True)

    for i, wi in enumerate(bytes_w):
        buckets[i % bins].append(wi)

    for wi in tensor_w:
        # TODO replace with headq
        idx = min(enumerate(bucket_sizes), key=operator.itemgetter(1))[0]
        buckets[idx].append(wi)
        bucket_sizes[idx] += _item_size(wi)

    return buckets