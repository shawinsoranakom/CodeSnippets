def movedim(self: list[int], source: list[int], destination: list[int]) -> list[int]:
    self_dim = len(self)
    if self_dim <= 1:
        return self
    normalized_src: list[int] = []
    normalized_dst: list[int] = []
    for i in range(len(source)):
        normalized_src.append(maybe_wrap_dim(source[i], self_dim))
        normalized_dst.append(maybe_wrap_dim(destination[i], self_dim))
    order = [-1 for i in range(self_dim)]
    src_dims = [i for i in range(self_dim)]
    dst_dims = [i for i in range(self_dim)]

    for i in range(len(source)):
        order[normalized_dst[i]] = normalized_src[i]
        src_dims[normalized_src[i]] = -1
        dst_dims[normalized_dst[i]] = -1

    source_dims: list[int] = []
    destination_dims: list[int] = []
    for ele in src_dims:
        if ele != -1:
            source_dims.append(ele)
    for ele in dst_dims:
        if ele != -1:
            destination_dims.append(ele)

    rest_dim = self_dim - len(source)
    for i in range(rest_dim):
        order[destination_dims[i]] = source_dims[i]
    return permute(self, order)