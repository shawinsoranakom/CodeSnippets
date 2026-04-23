def matmul(tensor1, tensor2, *, is_out=False):
    from torch.fx.experimental.symbolic_shapes import guard_or_false, guard_or_true

    dim_tensor1 = tensor1.dim()
    dim_tensor2 = tensor2.dim()
    if dim_tensor1 == 0 or dim_tensor2 == 0:
        raise AssertionError(
            f"matmul does not support 0-dimensional tensors, got dims: {dim_tensor1} and {dim_tensor2}"
        )
    if dim_tensor1 == 1 and dim_tensor2 == 1:
        return torch.dot(tensor1, tensor2)
    elif dim_tensor1 == 2 and dim_tensor2 == 1:
        return torch.mv(tensor1, tensor2)
    elif dim_tensor1 == 1 and dim_tensor2 == 2:
        return torch.squeeze(torch.mm(torch.unsqueeze(tensor1, 0), tensor2), 0)
    elif dim_tensor1 == 2 and dim_tensor2 == 2:
        return torch.mm(tensor1, tensor2)
    elif should_fold(tensor1, tensor2, is_out):
        # dim_tensor1 >=3 && (dim_tensor2 == 1 || dim_tensor2 == 2) ||
        # dim_tensor2 >=3 && (dim_tensor1 == 1 || dim_tensor1 == 2)
        # and some condition on the strides is fulfilled

        # optimization: use mm instead of bmm by folding the batch of the larger tensor
        # into its leading matrix dimension
        transpose = dim_tensor2 > dim_tensor1
        t1 = tensor2.mT if transpose else tensor1
        t2 = (
            tensor2 if not transpose else (tensor1.t() if dim_tensor1 == 2 else tensor1)
        )
        # Invariant: t1.dim() >= 3 && (t2.dim() == 1 || t2.dim() == 2)
        #            and t1 and t2 are matmul-compatible

        # Why not t1.view(-1, sizes_1[-1])?
        # If the last dim is 0, then view(-1, 0) won't work because the -1 becomes ambiguous.
        # This can happen in e.g. [3, 5, 0] @ [0, 0].
        sizes_1 = t1.shape
        output_shape = list(sizes_1[:-1])
        folded_dim1 = reduce(operator.mul, output_shape)

        # Readjust output_shape if we are multiplying by a matrix
        t2_is_matrix = t2.dim() == 2
        if t2_is_matrix:
            output_shape.append(t2.shape[1])

        # This will almost always be a view.
        # It may not be a view if t2->requires_grad(). See should_fold in aten/ for an explanation
        t1_folded = t1.reshape(folded_dim1, sizes_1[-1])
        if t2_is_matrix:
            # This copies if we perform a 2D @ 3D and the first tensor requires_grad
            # See should_fold native/LinearAlgebra.cpp for why.
            output = torch.ops.aten._unsafe_view(t1_folded.mm(t2), output_shape)
            return output.mT.contiguous() if transpose else output
        else:
            return torch.ops.aten._unsafe_view(t1_folded.mv(t2), output_shape)

    elif dim_tensor1 >= 1 and dim_tensor2 >= 1:
        # We are multiplying b1 x n x m1 by x2 x m2 x p (where b1 can be a list);
        # we track m1 vs m2 separately even though they must match for nicer error messages
        n = tensor1.size(-2) if dim_tensor1 > 1 else 1
        m1 = tensor1.size(-1)
        batch_tensor1 = tensor1.shape[:-2]
        m2 = tensor2.size(-2) if dim_tensor2 > 1 else tensor2.size(-1)
        p = tensor2.size(-1) if dim_tensor2 > 1 else 1

        batch_tensor2: list[int] = []
        # TODO: handling of slice
        for i in range(dim_tensor2 - 2):
            batch_tensor2.append(tensor2.size(i))

        # Same optimization for the gradients as that in should_fold
        # If we're going to broadcast, we force it to go through the should_fold branch
        if (
            dim_tensor1 == 3
            and dim_tensor2 == 3
            and guard_or_true(batch_tensor1[0] != batch_tensor2[0])
        ):
            if guard_or_false(batch_tensor1[0] == 1) and tensor1.requires_grad:
                return matmul(tensor1.squeeze(0), tensor2)
            if guard_or_false(batch_tensor2[0] == 1) and tensor2.requires_grad:
                return matmul(tensor1, tensor2.squeeze(0))

        # expand the batch portion (i.e. cut off matrix dimensions and expand rest)
        expand_batch_portion = list(
            torch.broadcast_shapes(batch_tensor1, batch_tensor2)
        )

        tensor1_expand_size = expand_batch_portion + [n, m1]

        expand_batch_product = prod(expand_batch_portion)

        # HACK: We need reshape with symint support
        tensor1_expanded = tensor1.expand(tensor1_expand_size).reshape(
            expand_batch_product, n, m1
        )

        vector_rhs = dim_tensor2 == 1
        if vector_rhs:
            tensor2_expand_size = expand_batch_portion + [m2]
            tensor2_expanded = (
                tensor2.expand(tensor2_expand_size)
                .reshape(expand_batch_product, m2)
                .unsqueeze(2)
            )
        else:
            tensor2_expand_size = expand_batch_portion + [m2, p]
            tensor2_expanded = tensor2.expand(tensor2_expand_size).reshape(
                expand_batch_product, m2, p
            )

        output_shape = expand_batch_portion
        if dim_tensor1 > 1:
            output_shape.append(n)

        if dim_tensor2 > 1:
            output_shape.append(p)

        if vector_rhs:
            return tensor1_expanded.bmm(tensor2_expanded).squeeze(-1).view(output_shape)
        else:
            return tensor1_expanded.bmm(tensor2_expanded).view(output_shape)
    else:
        torch._check(False, lambda: "both arguments to matmul need to be at least 1D")