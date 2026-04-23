def new(cls, dim: DimSpec, group_shape: tuple[int, ...], idx: int) -> DimSpec:
        from torch.fx.experimental.symbolic_shapes import guard_or_false, guard_or_true

        if not len(group_shape) > 0:
            raise AssertionError(
                f"Expected group_shape length > 0, got {len(group_shape)}"
            )
        if len(group_shape) == 1:
            # not really a group, just return the input dim back
            if not idx == 0:
                raise AssertionError(f"Expected idx == 0, got {idx}")
            return dim
        elif guard_or_false(group_shape[idx] == 1):
            return Singleton()
        else:
            # remove singletons from group
            # group_mapping = [(new_index, (shape, old_index)) ...]
            group_mapping = list(
                enumerate(
                    (s, i) for i, s in enumerate(group_shape) if guard_or_true(s != 1)
                )
            )
            new_group_shape = tuple(m[1][0] for m in group_mapping)
            new_idx = next(filter(lambda x: x[1][1] == idx, group_mapping))[0]
            return Split(dim, new_group_shape, new_idx)