def matmul(tensor1: list[int], tensor2: list[int]):
    dim_tensor1 = len(tensor1)
    dim_tensor2 = len(tensor2)
    if dim_tensor1 == 1 and dim_tensor2 == 1:
        return dot(tensor1, tensor2)
    elif dim_tensor1 == 2 and dim_tensor2 == 1:
        return mv(tensor1, tensor2)
    elif dim_tensor1 == 1 and dim_tensor2 == 2:
        return squeeze(mm(unsqueeze(tensor1, 0), tensor2), 0)
    elif dim_tensor1 == 2 and dim_tensor2 == 2:
        return mm(tensor1, tensor2)
    elif dim_tensor1 >= 1 and dim_tensor2 >= 1:
        # We are multiplying b1 x n x m1 by x2 x m2 x p (where b1 can be a list);
        # we track m1 vs m2 separately even though they must match for nicer error messages
        n = tensor1[-2] if dim_tensor1 > 1 else 1
        batch_tensor1: list[int] = []
        # TODO: handling of slice
        for i in range(dim_tensor1 - 2):
            batch_tensor1.append(tensor1[i])
        p = tensor2[-1]
        batch_tensor2: list[int] = []
        # TODO: handling of slice
        for i in range(dim_tensor2 - 2):
            batch_tensor2.append(tensor2[i])

        # expand the batch portion (i.e. cut off matrix dimensions and expand rest)
        expand_batch_portion = broadcast(batch_tensor1, batch_tensor2)

        # todo: copy ?
        output_shape = expand_batch_portion
        if dim_tensor1 > 1:
            output_shape.append(n)

        if dim_tensor2 > 1:
            output_shape.append(p)

        return output_shape
    else:
        raise AssertionError("both arguments to matmul need to be at least 1D")