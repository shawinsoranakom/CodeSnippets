def scatter_mm(blocks, others, indices_data, *, accumulators=None):
    """Scattered matrix multiplication of tensors.

    A scattered matrix multiplication is defined as a series of matrix
    multiplications applied to input tensors according to the input
    and output mappings specified by indices data.

    The following indices data formats are supported for defining a
    scattered matrix multiplication operation (:attr:`indices_data[0]`
    holds the name of the indices data format as specified below):

    - ``"scatter_mm"`` - matrix multiplications scattered in batches
      of tensors.

      If :attr:`blocks` is a :math:`(* \times M \times K) tensor,
      :attr:`others` is a :math:`(* \times K \times N)` tensor,
      :attr:`accumulators` is a :math:`(* \times M \times N)` tensor,
      and :attr:`indices = indices_data['indices']` is a :math:`(*
      \times 3)` tensor, then the operation is equivalent to the
      following code::

        c_offsets, pq = indices_data[1:]
        for r in range(len(c_offsets) - 1):
            for g in range(c_offsets[r], c_offsets[r + 1]):
                p, q = pq[g]
                accumulators[r] += blocks[p] @ others[q]

    - ``"bsr_strided_mm"`` - matrix multiplications scattered in
      batches of tensors and a tensor.

      If :attr:`blocks` is a :math:`(Ms \times Ks) tensor,
      :attr:`others` is a :math:`(* \times K \times N)` tensor,
      :attr:`accumulators` is a :math:`(* \times M \times N)` tensor, then
      the operation is equivalent to the following code::

        c_indices, r_offsets, p_offsets, q_offsets, meta = indices_data[1:]
        for b in range(nbatches):
            for i, r in enumerate(r_offsets):
                r0, r1 = divmod(r, N)
                acc = accumulators[b, r0 : r0 + Ms, r1 : r1 + Ns]
                for g in range(c_indices[i], c_indices[i + 1]):
                    p = p_offsets[g]
                    q0, q1 = divmod(q_offsets[g], N)
                    acc += blocks[p] @ others[b, q0 : q0 + Ks, q1 : q1 + Ns]

      where ``Ns = N // meta['SPLIT_N']``, and ``M`` and ``K`` are
      integer multiples of ``Ms`` and ``Ks``, respectively.

    - ``"bsr_strided_mm_compressed"`` - matrix multiplications
      scattered in batches of tensors and a tensor. A memory and
      processor efficient version of ``"bsr_strided_mm"`` format.  If
      :attr:`blocks` is a :math:`(Ms \times Ks) tensor, :attr:`others`
      is a :math:`(* \times K \times N)` tensor, :attr:`accumulators`
      is a :math:`(* \times M \times N)` tensor, then the operation is
      equivalent to the following code::

        c_indices, r_offsets, q_offsets, meta = indices_data[1:]
        for b in range(nbatches):
            for r in r_offsets:
                m = (r // N) // Ms
                n = (r % N) // Ns
                r0, r1 = divmod(r, N)
                c0, c1 = c_indices[m], c_indices[m + 1]
                acc = accumulators[b, r0 : r0 + Ms, r1 : r1 + Ns]
                for i, p in enumerate(range(c0, c1)):
                    q = q_offsets[n * c1 + (SPLIT_N - n) * c0 + i]
                    q0, q1 = divmod(q, N)
                    acc += blocks[p] @ others[b, q0 : q0 + Ks, q1 : q1 + Ns]

      where ``Ns = N // meta['SPLIT_N']``, and ``M`` and ``K`` are
      integer multiples of ``Ms`` and ``Ks``, respectively.

      Notice that the order of ``r_offsets`` items can be arbitrary;
      this property enables defining swizzle operators via
      rearrangements of ``r_offsets`` items..

    Auxiliary functions are provided for pre-computing
    :attr:`indices_data`. For example,
    :func:`bsr_scatter_mm_indices_data` is used to define indices data
    for matrix multiplication of BSR and strided tensors.

    Parameters
    ----------
    blocks (Tensor): a 3-D tensor of first matrices to be multiplied

    others (Tensor): a tensor of second matrices to be multiplied. If
      ``indices_data[0]=="scatter_mm"``, the tensor is a 1-D batch
      tensor of second input matrices to be multiplied. Otherwise, the
      second input matrices are slices of the :attr:`others` tensor.
    indices_data (tuple): a format data that defines the inputs and
      outputs of scattered matrix multiplications.

    Keyword arguments
    -----------------

    accumulators (Tensor, optional): a tensor of matrix product
      accumulators. If ``indices_data[0]=="scatter_mm"``, the tensor
      is a 1-D batch tensor of output matrices. Otherwise, output
      matrices are slices of the :attr:`accumulators` tensor.
    """
    indices_format = indices_data[0]

    if blocks.ndim != 3:
        raise AssertionError(f"blocks must be 3D, got {blocks.ndim}D")
    _P, Ms, Ks = blocks.shape

    if indices_format == "scatter_mm":
        c_offsets, pq = indices_data[1:]

        if others.ndim != 3:
            raise AssertionError(f"others must be 3D, got {others.ndim}D")
        _Q, Ks_, Ns = others.shape
        if Ks != Ks_:
            raise AssertionError(f"blocks K ({Ks}) != others K ({Ks_})")

        if accumulators is None:
            R = c_offsets.shape[0] - 1
            accumulators = torch.zeros(
                (R, Ms, Ns), dtype=blocks.dtype, device=blocks.device
            )
        else:
            R, Ms_, Ns_ = accumulators.shape
            if Ms_ != Ms:
                raise AssertionError(f"accumulators Ms ({Ms_}) != blocks Ms ({Ms})")
            if Ns_ != Ns:
                raise AssertionError(f"accumulators Ns ({Ns_}) != others Ns ({Ns})")

        if Ms % 16 or Ks % 16 or Ns % 16 or _scatter_mm2 is None:
            for r in range(c_offsets.shape[0] - 1):
                g0 = c_offsets[r]
                g1 = c_offsets[r + 1]
                for g in range(g0, g1):
                    p, q = pq[g]

                    accumulators[r] += blocks[p] @ others[q]
        else:
            _scatter_mm2(blocks, others, c_offsets, pq, accumulators)
        return accumulators

    elif indices_format == "bsr_strided_mm":
        others_shape = others.shape
        others = as1Dbatch(others)

        B, K, N = others.shape
        if K % Ks != 0:
            raise AssertionError(f"K ({K}) must be divisible by Ks ({Ks})")

        c_indices, r_offsets, p_offsets, q_offsets, meta = indices_data[1:]
        SPLIT_N = meta["SPLIT_N"]

        if accumulators is None:
            M = Ms + (r_offsets.max().item() + 1) // N
            accumulators = torch.zeros(
                (*others_shape[:-2], M, N), dtype=blocks.dtype, device=blocks.device
            )
        else:
            M, N_ = accumulators.shape[-2:]
            if N_ != N:
                raise AssertionError(f"accumulators N ({N_}) != others N ({N})")

        accumulators_shape = accumulators.shape
        accumulators = as1Dbatch(accumulators)

        Ns = N // SPLIT_N

        if Ms % 16 or Ks % 16 or Ns % 16 or _scatter_mm6 is None:
            accumulators.zero_()
            for b in range(B):
                for r in range(r_offsets.shape[0]):
                    r_ = r_offsets[r].item()
                    g0 = c_indices[r].item()
                    g1 = c_indices[r + 1].item()
                    r0, r1 = divmod(r_, N)
                    acc = accumulators[b, r0 : r0 + Ms, r1 : r1 + Ns]
                    for g in range(g0, g1):
                        p, q = p_offsets[g], q_offsets[g]
                        q0, q1 = divmod(q.item(), N)
                        acc += blocks[p] @ others[b, q0 : q0 + Ks, q1 : q1 + Ns]
        else:
            _scatter_mm6(
                blocks,
                others,
                c_indices,
                r_offsets,
                p_offsets,
                q_offsets,
                meta,
                accumulators,
            )
        return accumulators.view(accumulators_shape)

    elif indices_format == "bsr_strided_mm_compressed":
        others_shape = others.shape
        others = as1Dbatch(others)

        B, K, N = others.shape
        if K % Ks != 0:
            raise AssertionError(f"K ({K}) must be divisible by Ks ({Ks})")

        c_indices, r_offsets, q_offsets, meta = indices_data[1:]
        SPLIT_N = meta["SPLIT_N"]

        if accumulators is None:
            M = Ms + (r_offsets.max().item() + 1) // N
            accumulators = torch.zeros(
                (*others_shape[:-2], M, N), dtype=blocks.dtype, device=blocks.device
            )
        else:
            M, N_ = accumulators.shape[-2:]
            if N_ != N:
                raise AssertionError(f"accumulators N ({N_}) != others N ({N})")

        accumulators_shape = accumulators.shape
        accumulators = as1Dbatch(accumulators)

        Ns = N // SPLIT_N

        if Ms % 16 or Ks % 16 or Ns % 16 or _scatter_mm6 is None:
            for b in range(B):
                for j in range(len(r_offsets)):
                    r0, r1 = divmod(r_offsets[j].item(), N)
                    m = r0 // Ms
                    n = r1 // Ns
                    c0 = c_indices[m].item()
                    c1 = c_indices[m + 1].item()
                    acc = accumulators[b, r0 : r0 + Ms, r1 : r1 + Ns]
                    for i, p in enumerate(range(c0, c1)):
                        q = q_offsets[n * c1 + (SPLIT_N - n) * c0 + i].item()
                        q0, q1 = divmod(q, N)
                        acc += blocks[p] @ others[b, q0 : q0 + Ks, q1 : q1 + Ns]
        else:
            p_offsets = torch.empty(
                (0,), dtype=q_offsets.dtype, device=q_offsets.device
            )
            _scatter_mm6(
                blocks,
                others,
                c_indices,
                r_offsets,
                p_offsets,
                q_offsets,
                meta,
                accumulators,
            )
        return accumulators.view(accumulators_shape)

    else:
        raise NotImplementedError(indices_format)