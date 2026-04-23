def convert_to_strided_representation(args):
            """Convert differentiable non-strided tensors to a representation containing differentiable strided tensors."""
            if not isinstance(args, (list, tuple)):
                args = (args,)
            new_args: list[Any] = []
            for obj in args:
                if (
                    isinstance(obj, torch.Tensor)
                    and obj.requires_grad
                    and obj.layout in sparse_layouts
                ):
                    d = {
                        "layout": obj.layout,
                        "shape": obj.shape,
                    }
                    if not masked:
                        # Materialize unspecified elements with zero values
                        batch_dim = obj.ndim - obj.dense_dim() - obj.sparse_dim()
                        blocksize = (
                            obj.values().shape[batch_dim + 1 : batch_dim + 3]
                            if obj.layout in sparse_block_layouts
                            else None
                        )
                        full_mask = torch.ones(
                            obj.shape, device=obj.device, dtype=torch.bool
                        ).to_sparse(
                            layout=obj.layout,
                            blocksize=blocksize,
                            dense_dim=obj.dense_dim(),
                        )
                        obj = obj.to_dense().sparse_mask(full_mask)
                    if obj.layout is torch.sparse_coo:
                        # pyrefly: ignore [no-matching-overload]
                        d.update(
                            # pyrefly: ignore [bad-argument-type]
                            indices=obj._indices(),
                            # pyrefly: ignore [bad-argument-type]
                            is_coalesced=obj.is_coalesced(),
                        )
                        values = obj._values()
                    elif obj.layout in {torch.sparse_csr, torch.sparse_bsr}:
                        # pyrefly: ignore [no-matching-overload]
                        d.update(
                            # pyrefly: ignore [bad-argument-type]
                            compressed_indices=obj.crow_indices(),
                            # pyrefly: ignore [bad-argument-type]
                            plain_indices=obj.col_indices(),
                        )
                        values = obj.values()
                    else:
                        # pyrefly: ignore [no-matching-overload]
                        d.update(
                            # pyrefly: ignore [bad-argument-type]
                            compressed_indices=obj.ccol_indices(),
                            # pyrefly: ignore [bad-argument-type]
                            plain_indices=obj.row_indices(),
                        )
                        values = obj.values()
                    new_args.extend(
                        (STRIDED_REPRESENTATION, d, values.requires_grad_(True))
                    )
                else:
                    new_args.append(obj)
            return tuple(new_args)