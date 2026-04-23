def _nt_from_similar(self, other, dims):
        if len(dims) != other.dim():
            raise AssertionError(
                f"Expected len(dims) == other.dim(), got {len(dims)} != {other.dim()}"
            )
        if dims[0] != -1 and dims[0] != other.size(0):
            raise AssertionError(
                f"Expected dims[0] to be -1 or {other.size(0)}, got {dims[0]}"
            )

        ret_sizes = []
        for t in other.unbind():
            other_size = t.shape
            ret_size = []
            for i, d in enumerate(dims[1:]):
                if d == -1:
                    ret_size.append(other_size[i])
                else:
                    ret_size.append(d)
            ret_sizes.append(ret_size)

        return torch.nested.nested_tensor(
            [torch.randn(*size) for size in ret_sizes], device=other.device
        )