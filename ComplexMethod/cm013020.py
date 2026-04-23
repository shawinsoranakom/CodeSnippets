def index_put(
    g: jit_utils.GraphContext, self, indices_list_value, values, accumulate=False
):
    if symbolic_helper._is_packed_list(indices_list_value):
        indices_list = symbolic_helper._unpack_list(indices_list_value)
    else:
        indices_list = [indices_list_value]
    accumulate = symbolic_helper._parse_arg(accumulate, "b")

    if len(indices_list) == 0:
        return values

    if len(indices_list) > 1:
        for idx_ in range(len(indices_list)):
            if symbolic_helper._is_bool(indices_list[idx_]):
                indices_list[idx_] = g.op("NonZero", indices_list[idx_])
        index = indices_list[0]

        for ind in indices_list[1:]:
            index = opset9.add(g, index, ind)
        broadcast_index_shape = g.op("Shape", index)
        indices_list = [
            symbolic_helper._unsqueeze_helper(
                g, opset9.expand(g, ind, broadcast_index_shape, None), [-1]
            )
            for ind in indices_list
        ]
        index = g.op("Concat", *indices_list, axis_i=-1)
    else:
        # Replace index_put node with masked_scatter or masked_fill
        # when inputs to the index_put node contains a single boolean input.
        #
        # index_put -> masked_fill
        #   * input index contains single tensor of Bool type (e.g.: %24 <- %23).
        #   * input value contains single element (e.g.: %18).
        #
        # Torch IR
        #   %mask : Float(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu) = aten::clone(%0, %6)
        #   %16 : Bool(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu) =
        #               aten::to(%8, %26, %27, %11, %12, %28, %29, %15)
        #   %18 : Float(requires_grad=0, device=cpu) = prim::Constant[value={1}]()
        #   %23 : Bool(8, strides=[1], device=cpu) = aten::view(%16, %22)
        #   %24 : Tensor?[] = prim::ListConstruct(%23)
        #   %25 : Float(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu) =
        #                aten::index_put(%mask, %24, %18, %30)
        #   return (%25)
        #
        #
        # index_put -> masked_scatter
        #   * input index contains single tensor of Bool type (e.g.: %32 <- %31).
        #   * input value contains multiple elements (e.g.: %28).
        #
        # Torch IR
        #   %mask : Float(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu) = aten::clone(%0, %6)
        #   %28 : Float(8, strides=[1], requires_grad=0, device=cpu)
        #                = prim::Constant[value= 1  1  1  1  1  1  1  1 [ CPUFloatType{8} ]]()
        #   %15 : Bool(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu)
        #                = aten::ne(%mask, %some_const)
        #   %23 : Bool(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu)
        #                = aten::to(%15, %34, %35, %18, %19, %36, %37, %22)
        #   %38 : Long(requires_grad=0, device=cpu) = prim::Constant[value={0}]()
        #   %30 : int[] = prim::Constant[value=[-1]]()
        #   %31 : Bool(8, strides=[1], device=cpu) = aten::view(%23, %30)
        #   %32 : Tensor?[] = prim::ListConstruct(%31)
        #   %33 : Float(2, 2, 2, strides=[4, 2, 1], requires_grad=0, device=cpu)
        #               = aten::index_put(%mask, %32, %28, %38)
        #   return (%33)
        index = indices_list[0]
        bool_inp = index
        if symbolic_helper._is_bool(bool_inp):
            rank = symbolic_helper._get_tensor_rank(values)
            if rank is not None and rank == 0:
                return opset9.masked_fill(g, self, bool_inp, values)
            mask_rank = symbolic_helper._get_tensor_rank(bool_inp)
            self_rank = symbolic_helper._get_tensor_rank(self)
            if (
                mask_rank is not None
                and self_rank is not None
                and self_rank > mask_rank
            ):
                # Unsqueeze 'bool_inp' to be broadcastable to shape of 'self'.
                bool_inp = symbolic_helper._unsqueeze_helper(
                    g, bool_inp, list(range(mask_rank, self_rank))
                )
            return masked_scatter(g, self, bool_inp, values)
        broadcast_index_shape = g.op("Shape", index)
        index = symbolic_helper._unsqueeze_helper(g, index, [-1])
    sub_data_shape = symbolic_helper._slice_helper(
        g, g.op("Shape", self), axes=[0], starts=[len(indices_list)], ends=[sys.maxsize]
    )
    values_shape = g.op("Concat", broadcast_index_shape, sub_data_shape, axis_i=0)
    # Check if values is a singular value and expand accordingly
    rank = symbolic_helper._get_tensor_rank(values)
    if rank is not None and rank == 0:
        values = opset9.expand(g, values, values_shape, None)
    values = symbolic_helper._reshape_helper(g, values, values_shape)

    self_scalar_type = _type_utils.JitScalarType.from_value(
        self, _type_utils.JitScalarType.UNDEFINED
    )
    if self_scalar_type != _type_utils.JitScalarType.UNDEFINED:
        values_scalar_type = _type_utils.JitScalarType.from_value(
            values, _type_utils.JitScalarType.UNDEFINED
        )
        if self_scalar_type != values_scalar_type:
            values = g.op("Cast", values, to_i=self_scalar_type.onnx_type())
    elif accumulate:
        raise errors.SymbolicValueError("self does not have a valid scalar type.", self)

    if accumulate:
        zeros = g.op(
            "ConstantOfShape",
            g.op("Shape", self),
            value_t=torch.tensor([0], dtype=self_scalar_type.dtype()),
        )
        result = g.op("ScatterND", zeros, index, values)
        result = add(g, self, result)
    else:
        result = g.op("ScatterND", self, index, values)

    return result