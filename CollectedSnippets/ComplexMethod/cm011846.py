def fn(idx):
        assert len(idx) == len(output_size)
        assert len(indices_loaders) == len(indexed_size)

        rank = len(tensor_size)
        new_index = []
        first_tensor_index = tensor_indices[0]
        start_offset = 0 if non_consecutive_tensors else first_tensor_index
        next_idx = 0
        for i in range(tensor_indices[-1] + 1):
            if i == start_offset:
                next_idx += rank
            if indices[i] is None:
                assert next_idx < len(idx)
                new_index.append(idx[next_idx])
                next_idx += 1
            else:
                loader = indices_loaders[i]
                assert loader is not None
                size = indexed_size[i]
                new_index.append(
                    ops.indirect_indexing(
                        loader(idx[start_offset : start_offset + rank]),
                        size,
                        check=check,
                        wrap_neg=wrap_neg,
                    )
                )
        new_index = [
            *new_index,
            *idx[next_idx:],
        ]
        return new_index if x_loader is None else x_loader(new_index)