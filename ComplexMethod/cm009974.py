def index(
        self,
        dims: int | Dim | tuple[int | Dim, ...] | list[int | Dim],
        indices: int
        | slice
        | torch.Tensor
        | tuple[int | slice | torch.Tensor, ...]
        | list[int | slice | torch.Tensor],
    ) -> _Tensor:
        """
        Index tensor using first-class dimensions.
        """
        from ._dim_entry import _match_levels
        from ._getsetitem import getsetitem_flat, invoke_getitem
        from ._wrap import _wrap_dim

        # Helper to check if obj is a dimpack (tuple/list) and extract items
        def maybe_dimpack(obj: Any, check_first: bool = False) -> tuple[Any, bool]:
            if isinstance(obj, (tuple, list)):
                return list(obj), True
            return None, False

        def parse_dim_entry(s: Any) -> Any:
            d = _wrap_dim(s, self.ndim, False)
            if d.is_none():
                raise TypeError(f"expected a dimension specifyer but found {repr(s)}")
            return d

        # Helper for dimension not present errors
        def dim_not_present(d: Any) -> None:
            if d.is_positional():
                raise TypeError(
                    f"dimension {d.position() + self.ndim} not in tensor of {self.ndim} dimensions"
                )
            else:
                raise TypeError(f"dimension {repr(d.dim())} not in tensor")

        dims_list: list[int | Dim] = []
        indices_list: list[int | slice | torch.Tensor] = []

        lhs_list = isinstance(dims, (tuple, list))
        rhs_list = isinstance(indices, (tuple, list))

        if lhs_list and rhs_list:
            # Type narrowing: we know dims and indices are sequences here
            dims_seq = dims  # type: ignore[assignment]
            indices_seq = indices  # type: ignore[assignment]
            if len(dims_seq) != len(indices_seq):  # type: ignore[arg-type]
                raise TypeError(
                    f"dims ({len(dims_seq)}) and indices ({len(indices_seq)}) must have the same length"  # type: ignore[arg-type]
                )
            dims_list.extend(dims_seq)  # type: ignore[arg-type]
            indices_list.extend(indices_seq)  # type: ignore[arg-type]
        else:
            dims_list.append(dims)  # type: ignore[arg-type]
            indices_list.append(indices)  # type: ignore[arg-type]

        # Create tensor info
        self_info = TensorInfo.create(self, False, False)

        new_levels: list[Any] = []
        to_flatten: list[Any] = []
        dims_list_flat = []

        # Process each dim specification
        for i in range(len(dims_list)):
            m, is_dimpack = maybe_dimpack(dims_list[i], check_first=False)
            if is_dimpack:
                if len(m) == 0:
                    dims_list_flat.append(DimEntry())  # Empty dimpack
                    continue

                first = parse_dim_entry(m[0])
                dims_list_flat.append(first)

                if len(m) == 1:
                    continue

                # Multi-element dimpack requires flattening
                if len(to_flatten) == 0:
                    new_levels.extend(self_info.levels)

                rest = []
                for j in range(1, len(m)):
                    d = parse_dim_entry(m[j])
                    removed = False
                    for k in range(len(new_levels)):
                        if new_levels[k] == d:
                            new_levels.pop(k)
                            removed = True
                            break
                    if not removed:
                        dim_not_present(d)
                    rest.append(d)

                # Find first in new_levels
                first_idx = None
                for k in range(len(new_levels)):
                    if new_levels[k] == first:
                        first_idx = k
                        break
                if first_idx is None:
                    dim_not_present(first)
                    continue  # Skip this iteration if dimension not found

                for j, r in enumerate(rest):
                    new_levels.insert(first_idx + 1 + j, r)
                to_flatten.extend(rest)
            else:
                dims_list_flat.append(parse_dim_entry(dims_list[i]))

        # Handle dimension flattening if needed
        if len(to_flatten) > 0:
            if self_info.tensor is None:
                raise AssertionError(
                    "Cannot perform dimension flattening on None tensor"
                )
            rearranged = _match_levels(self_info.tensor, self_info.levels, new_levels)
            sizes = rearranged.size()
            new_sizes: list[Any] = []
            reshape_levels = []

            for i in range(len(new_levels)):
                if new_levels[i] in to_flatten:
                    if len(new_sizes) == 0:
                        new_sizes.append(sizes[i])
                    else:
                        new_sizes[-1] *= sizes[i]
                else:
                    new_sizes.append(sizes[i])
                    reshape_levels.append(new_levels[i])

            self_info.tensor = rearranged.reshape(new_sizes)
            self_info.levels = reshape_levels

        # Check for dimpacks in indices
        has_dimpacks = False
        for idx in indices_list:
            if isinstance(idx, (tuple, list)):
                has_dimpacks = True
                break

        # Call getsetitem_flat with correct parameters
        info = getsetitem_flat(
            self_info,
            [],  # empty input_list
            dims_list_flat,  # keys
            indices_list,  # values
            has_dimpacks,
        )

        return invoke_getitem(info)