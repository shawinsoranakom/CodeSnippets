def _group_tensors_by_device_dtype_and_is_multidim(
    tensorlists: TensorListList,
) -> dict[
    tuple[torch.device | None, torch.dtype | None, bool],
    list[list[Tensor | None]],
]:
    """Groups tensors by device, dtype, AND multidimensionality -- whether the tensor
    has multiple dims or just one dim (is a vector). This allows the foreach impl of
    Adafactor to assume that every group of params will either be factored or not."""
    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(tensorlists)
    ultra_grouped_tensors: dict[
        tuple[torch.device | None, torch.dtype | None, bool],
        list[list[Tensor | None]],
    ] = {}
    for (device, dtype), (tensorlists, _) in grouped_tensors.items():
        matrix_key = (device, dtype, True)
        vector_key = (device, dtype, False)

        # assumes grad is the second tensorlist
        for j, tensor in enumerate(tensorlists[1]):
            if tensor is None:
                raise AssertionError("grad should not be None")
            if tensor.dim() > 1:
                if matrix_key not in ultra_grouped_tensors:
                    ultra_grouped_tensors[matrix_key] = [[] for _ in tensorlists]
                for i in range(len(tensorlists)):
                    ultra_grouped_tensors[matrix_key][i].append(tensorlists[i][j])
            else:
                if vector_key not in ultra_grouped_tensors:
                    ultra_grouped_tensors[vector_key] = [[] for _ in tensorlists]
                for i in range(len(tensorlists)):
                    ultra_grouped_tensors[vector_key][i].append(tensorlists[i][j])
    return ultra_grouped_tensors