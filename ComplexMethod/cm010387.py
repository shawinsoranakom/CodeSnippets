def _scan(init, xs):
        """Perform scan on `elems` using `elems_init."""
        carry = init
        if len(xs) == 0:
            return carry, []

        num_elems = xs[0].shape[dim]
        num_init_leaves = len(init)

        # Process element 0 to infer output shapes for pre-allocation
        # AND produce the first real result in a single call.  The previous
        # approach used first_slice_copy() for shape inference and then
        # re-processed element 0 in the main loop, calling the operator
        # num_elems+1 times.  That extra invocation is incorrect for
        # operators with side effects.
        carry, out_0 = _extract_carry_and_out(
            call_operator(
                operator,
                *carry,
                *[elem.select(dim, 0) for elem in xs],
                *additional_inputs,
            ),
            num_init_leaves,
        )

        out_tensor_mask = get_tensor_mask(out_0)
        out_0_masked = mask_list(out_tensor_mask, out_0)

        # Pre-allocate
        # outs -> Output matrix
        # idxs -> Index matrix for scatter_
        # out: (num_elems, M, N, ...)
        # idx: (1, M, N)
        outs = [
            torch.empty(
                [num_elems] + list(e.size()),
                dtype=e.dtype,
                device=e.device,
            )
            for e in out_0_masked
        ]
        idxs = [
            torch.ones_like(e, dtype=torch.int64).unsqueeze(0) for e in out_0_masked
        ]

        def store_out_in_outs(out, ind):
            # Store the intermediate out in the outs matrix
            for o, x, idx in zip(outs, out, idxs):
                # o: (num_elems, M, N ...)
                # x: (M, N, ...) -> (1, M, N)
                # ind * idx: (1, M, N,) with values to be ind
                # essentially: o[ind][n][k] = x[0][n][k]
                o.scatter_(0, ind * idx, x.unsqueeze(0))

        # Store element 0's result, then continue from element 1.
        store_out_in_outs(out_0_masked, 0)

        for i in range(1, num_elems):
            carry, out = _extract_carry_and_out(
                call_operator(
                    operator,
                    *carry,
                    *[elem.select(dim, i) for elem in xs],
                    *additional_inputs,
                ),
                num_init_leaves,
            )

            store_out_in_outs(mask_list(out_tensor_mask, out), i)

        # Expand outs with None depending on the tensor mask of the output
        outs_expanded = [outs.pop(0) if out_m else None for out_m in out_tensor_mask]

        return (*carry, *outs_expanded)