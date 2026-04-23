def has_mutated(
            before: Any, after: Any, md: tuple[tuple[int, ...], int] | None
        ) -> bool:
            are_tensors = type(before) is torch.Tensor and type(after) is torch.Tensor
            if (
                are_tensors
                and before.layout != torch.sparse_csr
                and after.layout != torch.sparse_csr
            ):
                return md is not None and not (
                    before.size() == after.size()
                    and bitwise_equal(before, after)
                    and md[0] == after.stride()
                    and md[1] == after._typed_storage()._cdata
                )
            return False