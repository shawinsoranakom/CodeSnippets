def map_arg(arg):
        def maybe_non_contig(tensor):
            if not non_contiguous or tensor.numel() < 2:
                return tensor.clone()

            return noncontiguous_like(tensor)

        def conjugate(tensor):
            return tensor.conj()

        if isinstance(arg, (torch.Size, dont_convert)):
            return arg
        elif isinstance(arg, tuple) and len(arg) == 0:
            var = conjugate(torch.randn((), dtype=dtype, device=device))
            var.requires_grad = requires_grad
            return var
        elif isinstance(arg, tuple) and not isinstance(arg[0], torch.Tensor):
            return conjugate(maybe_non_contig(torch.randn(*arg, dtype=dtype, device=device))).requires_grad_(requires_grad)
        # double check casting
        elif isinstance(arg, non_differentiable):
            if isinstance(arg.tensor, torch.Tensor):
                return conjugate(maybe_non_contig(arg.tensor.to(device=device)))
            return conjugate(maybe_non_contig(arg.tensor.to(device=device)))
        elif isinstance(arg, torch.Tensor):
            if arg.is_complex() != dtype.is_complex:
                raise RuntimeError("User provided tensor is real for a test that runs with complex dtype, ",
                                   "which is not supported for now")
            # NOTE: We do clone() after detach() here because we need to be able to change size/storage of v afterwards
            v = conjugate(maybe_non_contig(arg)).detach().to(device=device).clone()
            v.requires_grad = requires_grad and (v.is_floating_point() or v.is_complex())
            return v
        elif callable(arg):
            return map_arg(arg(dtype=dtype, device=device))
        else:
            return arg