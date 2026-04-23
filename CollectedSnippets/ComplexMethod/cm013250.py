def get_batch_sparse_data(pattern, blocksize):
            size = pattern.shape
            if len(size) <= 2:  # non-batch
                return get_sparse_data_with_block(pattern, blocksize)

            # batch data is created recursively:
            batch_data = {}  # type: ignore[var-annotated]
            for i, item in enumerate(pattern):
                for layout, d in get_batch_sparse_data(item, blocksize).items():
                    target = batch_data.get(layout)
                    if layout is torch.sparse_coo:
                        # a "batch COO" means a COO with the leading
                        # sparse dimensions interpreted as batch
                        # dimensions
                        ext_coo_indices1 = torch.cat((torch.full((1, len(d[1])), i, dtype=torch.int64), d[0]))
                        if target is None:
                            target = batch_data[layout] = (ext_coo_indices1, d[1])
                        else:
                            target[0].set_(torch.cat((target[0], ext_coo_indices1), 1))  # type: ignore[call-overload]
                            target[1].set_(torch.cat((target[1], d[1])))
                    else:
                        if target is None:
                            target = batch_data[layout] = tuple(d[j].unsqueeze(0) for j in range(len(d)))
                        else:
                            for j in range(len(d)):
                                target[j].set_(torch.cat((target[j], d[j].unsqueeze(0))))  # type: ignore[call-overload]
            return batch_data