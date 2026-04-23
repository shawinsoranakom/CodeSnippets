def compute_jacobian_preallocate_and_copy() -> list[Any]:
            # Helper function to compute chunked Jacobian
            # The intermediate chunked calculation are only
            # scoped at this function level.
            out_vec_size = sum(flat_output_numels)

            # Don't pre-allocate if we have a single chunk.
            stacked_results: list[torch.Tensor] = []
            if not (chunk_size is None or chunk_size >= out_vec_size):
                stacked_results = [
                    primal.new_zeros(out_vec_size, *primal.shape)
                    for primal in flat_primals
                ]

            for idx, flat_basis_chunk in enumerate(
                _chunked_standard_basis_for_(
                    flat_output, flat_output_numels, chunk_size=chunk_size
                )
            ):
                if chunk_size == 1:
                    # sanity check.
                    for t in flat_basis_chunk:
                        if t.size(0) != 1:
                            raise AssertionError(
                                f"expected t.size(0) to be 1, got {t.size(0)}"
                            )

                    flat_basis_chunk = [torch.squeeze(t, 0) for t in flat_basis_chunk]

                basis = tree_unflatten(flat_basis_chunk, output_spec)

                if chunk_size == 1:
                    # Behaviour with `chunk_size=1` is same as `for-loop`
                    # i.e. user shouldn't deal with the limitations of vmap.
                    chunked_result = vjp_fn(basis)
                else:  # chunk_size is None or chunk_size != 1
                    chunked_result = vmap(vjp_fn)(basis)

                flat_results = pytree.tree_leaves(chunked_result)

                # Short-circuit if we have a single chunk.
                if chunk_size is None or chunk_size >= out_vec_size:
                    if chunk_size == 1:  # and out_vec_size == 1
                        # Since we squeezed the output dim
                        flat_results = tree_map(
                            lambda t: torch.unsqueeze(t, 0), flat_results
                        )
                    return flat_results

                for r, sr in zip(flat_results, stacked_results):  # type: ignore[possibly-unbound]
                    sr[idx * chunk_size : (idx + 1) * chunk_size].copy_(r)

            return stacked_results