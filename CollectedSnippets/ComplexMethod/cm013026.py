def atleast_3d(g: jit_utils.GraphContext, self: torch._C.Value):
    # NOTE: If it's 0D, reshape to 3D
    #       If it's 1D, unsqueeze to 3D
    #       If it's 2D, unsqueeze to 3D

    # NOTE: self could be a packed list or a tensor
    if symbolic_helper._is_value(self) and symbolic_helper._is_packed_list(self):
        tensor_list = symbolic_helper._unpack_list(self)
        new_tensor_list = []
        for tensor in tensor_list:
            new_tensor = tensor
            tensor_rank = symbolic_helper._get_tensor_rank(tensor)
            if tensor_rank == 0:
                new_tensor = symbolic_helper._reshape_helper(
                    g, new_tensor, g.op("Constant", value_t=torch.tensor([1, 1, 1]))
                )
            elif tensor_rank == 1:
                new_tensor = symbolic_helper._unsqueeze_helper(
                    g, new_tensor, axes_i=[0]
                )
                new_tensor = symbolic_helper._unsqueeze_helper(
                    g, new_tensor, axes_i=[-1]
                )
            elif tensor_rank == 2:
                new_tensor = symbolic_helper._unsqueeze_helper(
                    g, new_tensor, axes_i=[-1]
                )
            new_tensor_list.append(new_tensor)
        return g.op("SequenceConstruct", *new_tensor_list)

    tensor_rank = symbolic_helper._get_tensor_rank(self)
    if tensor_rank == 0:
        self = symbolic_helper._reshape_helper(
            g, self, g.op("Constant", value_t=torch.tensor([1, 1, 1]))
        )
    elif tensor_rank == 1:
        self = symbolic_helper._unsqueeze_helper(g, self, axes_i=[0])
        self = symbolic_helper._unsqueeze_helper(g, self, axes_i=[-1])
    elif tensor_rank == 2:
        self = symbolic_helper._unsqueeze_helper(g, self, axes_i=[-1])
    return self