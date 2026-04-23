def __getitem__(self, indices):
        data = self.output
        rank = len(data.get_partial_shape())
        axes, gather_indices_nodes = [], []
        slice_axes, slice_starts, slice_ends, slice_steps = [], [], [], []
        unsqueeze_axes = []

        if not isinstance(indices, tuple):
            indices = (indices,)

        if any(i is Ellipsis for i in indices):
            ellipsis_pos = indices.index(Ellipsis)
            num_specified = sum(
                i is not Ellipsis and i is not None for i in indices
            )
            num_missing = rank - num_specified
            indices = (
                indices[:ellipsis_pos]
                + (builtins.slice(None),) * num_missing
                + indices[ellipsis_pos + 1 :]
            )

        def count_unsqueeze_before(dim):
            return sum(1 for i in range(dim) if indices[i] is None)

        partial_shape = ov_opset.shape_of(data, Type.i32)
        zero_const = ov_opset.constant(0, Type.i32)

        for dim, index in enumerate(indices):
            if isinstance(index, bool):
                raise ValueError(
                    "OpenVINO backend does not support boolean indexing"
                )
            elif isinstance(index, (int, np.integer, np.ndarray)):
                if isinstance(index, (np.ndarray, np.integer)):
                    if isinstance(index, np.ndarray) and len(index.shape) != 0:
                        raise ValueError(
                            "OpenVINO backend does not support"
                            "multi-dimensional indexing"
                        )
                    index = int(index)
                actual_dim = dim - count_unsqueeze_before(dim)
                if not (0 <= actual_dim < rank):
                    raise IndexError(
                        f"Index {index} is out of bounds for "
                        f"axis {dim} with rank {rank}"
                    )
                length = ov_opset.gather(
                    partial_shape,
                    ov_opset.constant([actual_dim], Type.i32),
                    zero_const,
                )
                if index >= 0:
                    idx_value = ov_opset.constant([index], Type.i32)
                else:
                    idx_value = ov_opset.add(
                        ov_opset.constant([index], Type.i32), length
                    )
                axes.append(dim)
                gather_indices_nodes.append(idx_value.output(0))
            elif isinstance(index, builtins.slice):
                if (
                    index.start is None
                    and index.stop is None
                    and index.step is None
                ):
                    continue
                if (
                    index.step is not None
                    and not isinstance(index.step, OpenVINOKerasTensor)
                    and index.step < 0
                ):
                    raise ValueError("OpenVINO doesn't support negative steps")
                slice_axes.append(dim)
                slice_starts.append(0 if index.start is None else index.start)
                slice_ends.append(
                    2**31 - 1 if index.stop is None else index.stop
                )
                slice_steps.append(1 if index.step is None else index.step)
            elif index is None:
                unsqueeze_axes.append(dim)
            elif isinstance(index, OpenVINOKerasTensor):
                index = get_ov_output(index)
                index_type = index.get_element_type()
                index_shape = index.get_partial_shape()
                if index_type == Type.boolean or not index_type.is_integral():
                    raise ValueError(
                        "OpenVINO backend does not "
                        f"support {index_type} indexing"
                    )
                axes.append(dim)
                if len(index_shape) > 1:
                    raise ValueError(
                        "OpenVINO backend does not "
                        "support multi-dimensional indexing"
                    )
                if len(index_shape) == 0:
                    index = ov_opset.unsqueeze(index, zero_const).output(0)
                if index_type != Type.i32:
                    index = ov_opset.convert(index, Type.i32).output(0)
                shape_tensor = ov_opset.shape_of(data, Type.i32)
                axis_i32 = ov_opset.constant([dim], dtype=Type.i32)
                dim_size = ov_opset.gather(shape_tensor, axis_i32, zero_const)
                is_negative = ov_opset.less(index, zero_const)
                adjusted_index = ov_opset.add(index, dim_size)
                index = ov_opset.select(
                    is_negative, adjusted_index, index
                ).output(0)
                gather_indices_nodes.append(index)
            else:
                raise ValueError(
                    f"Unsupported index type {type(index)} "
                    "in OpenVINOKerasTensor.__getitem__"
                )

        if slice_axes:

            def _to_slice_bound(values, dtype=Type.i32):
                nodes = []
                for v in values:
                    if isinstance(v, OpenVINOKerasTensor):
                        node = v.output
                    else:
                        node = ov_opset.constant([v], dtype).output(0)
                    if node.get_element_type() != dtype:
                        node = ov_opset.convert(node, dtype).output(0)
                    ps = node.get_partial_shape()
                    if len(ps) == 0:
                        node = ov_opset.unsqueeze(
                            node, ov_opset.constant(0, Type.i32)
                        ).output(0)
                    nodes.append(node)
                if len(nodes) == 1:
                    return nodes[0]
                return ov_opset.concat(nodes, axis=0).output(0)

            step = _to_slice_bound(slice_steps)
            start = _to_slice_bound(slice_starts)
            stop = _to_slice_bound(slice_ends)
            adjusted_slice_axes = [
                ax - sum(1 for unsq in unsqueeze_axes if unsq <= ax)
                for ax in slice_axes
            ]
            axes_const = ov_opset.constant(
                adjusted_slice_axes, Type.i32
            ).output(0)
            data = ov_opset.slice(data, start, stop, step, axes_const).output(0)

        if axes:
            gather_indices_const = (
                gather_indices_nodes[0]
                if len(gather_indices_nodes) == 1
                else ov_opset.concat(gather_indices_nodes, axis=0).output(0)
            )
            adjusted_axes = [
                ax - sum(1 for unsq in unsqueeze_axes if unsq <= ax)
                for ax in axes
            ]
            if len(axes) == 1:
                data = ov_opset.gather(
                    data, gather_indices_const, adjusted_axes[0]
                ).output(0)
                data = ov_opset.squeeze(data, adjusted_axes[0]).output(0)
            else:
                rank = len(data.get_partial_shape())
                remaining_axes = [
                    i for i in range(rank) if i not in adjusted_axes
                ]
                perm = ov_opset.constant(
                    adjusted_axes + remaining_axes, Type.i32
                )
                data = ov_opset.transpose(data, perm).output(0)
                data = ov_opset.gather_nd(data, gather_indices_const).output(0)

        if unsqueeze_axes:
            adjusted_unsqueeze = []
            for ax in unsqueeze_axes:
                ax -= sum(1 for s in axes if s < ax)
                ax -= sum(1 for s in slice_axes if s < ax)
                adjusted_unsqueeze.append(ax)
            unsqueeze_const = ov_opset.constant(
                adjusted_unsqueeze, Type.i32
            ).output(0)
            data = ov_opset.unsqueeze(data, unsqueeze_const).output(0)

        return OpenVINOKerasTensor(data)