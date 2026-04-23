def index(g: jit_utils.GraphContext, self, index):
    if symbolic_helper._is_packed_list(index):
        indices = symbolic_helper._unpack_list(index)
    else:
        indices = [index]

    def try_mask_to_index(index):
        if not symbolic_helper._is_none(index) and (
            _type_utils.JitScalarType.from_value(
                index, _type_utils.JitScalarType.UNDEFINED
            )
            == _type_utils.JitScalarType.UINT8
            or symbolic_helper._is_bool(index)
        ):
            if g.opset < 9:
                raise errors.SymbolicValueError(
                    "Exporting masked indices are only supported after ONNX opset 9.",
                    self,
                )
            warnings.warn(
                "Exporting aten::index operator with indices of type Byte. "
                "Only 1-D indices are supported. In any other case, "
                "this will produce an incorrect ONNX graph.",
                stacklevel=2,
            )
            index = symbolic_helper._squeeze_helper(g, nonzero(g, index), [1])
        return index

    indices = [try_mask_to_index(idx) for idx in indices]
    if len(indices) == 1:
        return symbolic_helper._select_helper(
            g, self, 0, indices[0], apply_reshape=False
        )
    else:
        # Multiple tensors as indices. Each tensor could either be
        #   1. prim::Constant()
        #           representing ":" in python indexing. E.g. tensor[:, :]
        #   2. prim::Constant[value=...] or tensor output
        #           representing advanced indexing. E.g. tensor[[0, 1], [2, 0]].
        # For more info on advanced indexing,
        # check https://numpy.org/doc/stable/user/basics.indexing.html#advanced-indexing

        # Consider a general case of
        #       t: [x_1, y_1, y_2, ..., x_m, ..., y_n]
        # where t is a tensor of rank m+n, {x_i} are axes where tensor index is provided, and {y_i} are axes for ":".
        # Same results can be achieved through transposing t into
        #       t: [x_1, x_2, ..., x_m, y_1, y_2, ..., y_n]
        # and use gatherND. However ONNX does not have gatherND, to use 1d gather we'll need to flatten t
        # and process the tensor indices.
        #       t: [x_1 * x_2 * ... * x_m, y_1 * y_2 * ... * y_n]
        #       tensor index = \sum_{i=1}^m (ind_i * \prod_{j=i+1}^m (x_j))
        # After gather, reshape and transpose back.
        adv_idx_indices = [
            i for i, idx in enumerate(indices) if not symbolic_helper._is_none(idx)
        ]

        if len(adv_idx_indices) == 0:
            return self
        elif len(adv_idx_indices) == 1:
            return index_select(
                g, self, adv_idx_indices[0], indices[adv_idx_indices[0]]
            )
        else:
            rank = symbolic_helper._get_tensor_rank(self)
            if rank is None:
                return symbolic_helper._unimplemented(
                    "aten::index",
                    "operator of advanced indexing on tensor of unknown rank. ",
                    self,
                )
            # TODO: If indexing is supported natively in ONNX in future opsets,
            #       update the warning to recommend exporting with higher opset version.
            warnings.warn(
                "Exporting aten::index operator of advanced indexing in opset "
                f"{GLOBALS.export_onnx_opset_version}"
                " is achieved by combination of multiple ONNX operators, "
                "including Reshape, Transpose, Concat, and Gather. "
                "If indices include negative values, the exported graph will produce incorrect results.",
                stacklevel=2,
            )
            adv_idx_count = len(adv_idx_indices)
            shape_tensor = _shape_as_tensor(g, self)
            dim_tensor_list = [
                g.op(
                    "Gather",
                    shape_tensor,
                    g.op("Constant", value_t=torch.LongTensor([dim])),
                    axis_i=0,
                )
                for dim in range(rank)
            ]

            self = g.op(
                "Transpose",
                self,
                perm_i=adv_idx_indices
                + [i for i in range(rank) if i not in adv_idx_indices],
            )
            self = g.op("Flatten", self, axis_i=adv_idx_count)

            # Note that tensor indices will be broadcasted while accumulating. Thus we get the final subarray shape as well.
            cum_adv_index = indices[adv_idx_indices[-1]]
            multiplier = dim_tensor_list[adv_idx_indices[-1]]
            for i in range(adv_idx_count - 2, -1, -1):
                adv_index = g.op("Mul", indices[adv_idx_indices[i]], multiplier)
                cum_adv_index = g.op("Add", cum_adv_index, adv_index)
                multiplier = g.op(
                    "Mul", multiplier, dim_tensor_list[adv_idx_indices[i]]
                )

            # perform gather
            self = index_select(g, self, 0, cum_adv_index)

            cum_adv_index_shape_tensor = _shape_as_tensor(g, cum_adv_index)
            # check if all advanced indices are consecutive.
            # Refer to https://numpy.org/doc/stable/user/basics.indexing.html#combining-advanced-and-basic-indexing
            # to understand how the subarray position is decided.
            if adv_idx_indices == list(
                range(adv_idx_indices[0], adv_idx_indices[-1] + 1)
            ):
                # unfold regular index axes
                folded_adv_idx_shape_list = [
                    g.op("Constant", value_t=torch.LongTensor([-1]))
                ] + [
                    dim_tensor_list[i] for i in range(rank) if i not in adv_idx_indices
                ]
                folded_adv_idx_shape = g.op(
                    "Concat", *folded_adv_idx_shape_list, axis_i=0
                )
                self = symbolic_helper._reshape_helper(g, self, folded_adv_idx_shape)

                # Transpose folded advanced indexed axis to its original location.
                adv_idx_permute = (
                    list(range(1, adv_idx_indices[0] + 1))
                    + [0]
                    + list(range(adv_idx_indices[0] + 1, rank - adv_idx_count + 1))
                )
                self = g.op("Transpose", self, perm_i=adv_idx_permute)

                # unfold advanced index axes
                final_shape_list = (
                    [dim_tensor_list[i] for i in range(adv_idx_indices[0])]
                    + [cum_adv_index_shape_tensor]
                    + [
                        dim_tensor_list[i]
                        for i in range(adv_idx_indices[0], rank)
                        if i not in adv_idx_indices
                    ]
                )
                final_shape = g.op("Concat", *final_shape_list, axis_i=0)
            else:
                final_shape = g.op(
                    "Concat",
                    cum_adv_index_shape_tensor,
                    *[
                        dim_tensor_list[i]
                        for i in range(rank)
                        if i not in adv_idx_indices
                    ],
                    axis_i=0,
                )

            return symbolic_helper._reshape_helper(g, self, final_shape)