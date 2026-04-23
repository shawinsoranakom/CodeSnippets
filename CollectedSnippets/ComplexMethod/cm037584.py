def matmul_batch_invariant(a, b, *, out=None):
    # torch.matmul can handle various dimensions
    # For 2D x 2D, it's the same as mm
    if a.ndim == 2 and b.ndim == 2:
        result = matmul_persistent(a, b)
        if out is not None:
            out.copy_(result)
            return out
        return result
    elif b.ndim == 2:
        # Handle ND x 2D: Common for linear layers
        # (..., batch, seq, hidden) @ (hidden, out) -> (..., batch, seq, out)
        batch_dims = a.shape[:-1]
        hidden = a.shape[-1]
        out_dim = b.shape[-1]
        a_2d = a.reshape(-1, hidden)
        result_2d = matmul_persistent(a_2d, b)
        result = result_2d.reshape(batch_dims + (out_dim,))
        if out is not None:
            out.copy_(result)
            return out
        return result
    elif a.ndim >= 2 and b.ndim >= 3:
        # Generic handler for 2D x ND and ND x ND (except 1D)
        # Broadcast dims to ensure both matrices have the same shape
        # If 2D x ND, then unsqueeze to add a dim to a
        if a.ndim == 2:
            a = a.unsqueeze(0)
        broadcast_shape = torch.broadcast_shapes(a.shape[:-2], b.shape[:-2])
        a = a.expand(broadcast_shape + a.shape[-2:])
        b = b.expand(broadcast_shape + b.shape[-2:])
        batch_dim = math.prod(broadcast_shape)
        # Reuse broadcast shape to get all dims except mm dims
        a_3d = a.reshape(batch_dim, a.shape[-2], a.shape[-1])
        b_3d = b.reshape(batch_dim, b.shape[-2], b.shape[-1])
        # Do batched matmul
        result_3d = bmm_batch_invariant(a_3d, b_3d)
        # Reshape back to [broadcast_shape, seq_a, seq_b]
        result = result_3d.reshape(broadcast_shape + (a.shape[-2], b.shape[-1]))
        if out is not None:
            out.copy_(result)
            return out
        return result
    else:
        raise ValueError(
            f"matmul_batch_invariant requires both inputs be at least 2D "
            f"got shapes {a.shape} and {b.shape}"
        )