def diag(x, k=0):
    x = get_ov_output(x)
    x_shape = x.get_partial_shape()
    rank = x_shape.rank.get_length()

    if rank == 1:
        N_dim = x_shape[0]
        if not N_dim.is_static:
            raise ValueError(
                "diag requires input with static shape for 1D input."
            )
        N = N_dim.get_length()
        output_size = N + np.abs(k)
        out_shape = ov_opset.constant(
            [output_size, output_size], dtype=Type.i32
        ).output(0)
        zeros_const = ov_opset.constant(0, x.get_element_type()).output(0)
        diag_matrix = ov_opset.broadcast(zeros_const, out_shape)

        indices = []
        if k >= 0:
            for i in range(N):
                indices.append([i, i + k])
        else:
            for i in range(N):
                indices.append([i - k, i])

        indices = np.array(indices, dtype=np.int32)
        indices_const = ov_opset.constant(indices, dtype=Type.i32).output(0)
        updated = ov_opset.scatter_nd_update(diag_matrix, indices_const, x)
        return OpenVINOKerasTensor(updated.output(0))

    elif rank == 2:
        M_dim = x_shape[0]
        N_dim = x_shape[1]
        if not M_dim.is_static or not N_dim.is_static:
            raise ValueError(
                "diag requires input with static shape for 2D input."
            )
        M = M_dim.get_length()
        N = N_dim.get_length()

        if k >= 0:
            L = np.minimum(M, N - k) if (N - k) > 0 else 0
            indices = [[i, i + k] for i in range(L)]
        else:
            L = np.minimum(M + k, N) if (M + k) > 0 else 0
            indices = [[i - k, i] for i in range(L)]

        if L <= 0:
            keras_dtype = ov_to_keras_type(x.get_element_type())
            np_dtype = np.dtype(keras_dtype)
            empty_np = np.empty((0,), dtype=np_dtype)
            empty_const = ov_opset.constant(
                empty_np, x.get_element_type()
            ).output(0)
            return OpenVINOKerasTensor(empty_const)

        indices = np.array(indices, dtype=np.int32)
        indices_const = ov_opset.constant(indices, dtype=Type.i32).output(0)
        diag_vec = ov_opset.gather_nd(x, indices_const)
        return OpenVINOKerasTensor(diag_vec.output(0))

    else:
        raise ValueError("diag supports only 1D or 2D tensors")