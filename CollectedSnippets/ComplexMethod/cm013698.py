def forward(ctx, destination, num_inputs, *grads):
        ctx.target_gpus = [
            grads[i].get_device() for i in range(0, len(grads), num_inputs)
        ]

        complex_mask = [grads[i].is_complex() for i in range(num_inputs)]
        ctx.complex_mask = complex_mask

        grads_converted = tuple(
            torch.view_as_real(g) if g.is_complex() else g for g in grads
        )

        grads_ = [
            grads_converted[i : i + num_inputs]
            for i in range(0, len(grads_converted), num_inputs)
        ]
        results = comm.reduce_add_coalesced(grads_, destination)

        results = tuple(
            torch.view_as_complex(r) if is_complex else r
            for r, is_complex in zip(results, complex_mask)
        )

        return results