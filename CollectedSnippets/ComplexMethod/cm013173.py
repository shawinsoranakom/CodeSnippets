def noncontiguize(self, obj):
        if isinstance(obj, list):
            return [self.noncontiguize(o) for o in obj]
        elif isinstance(obj, tuple):
            return tuple(self.noncontiguize(o) for o in obj)
        tensor = obj
        ndim = tensor.dim()
        # Always making only the last dimension noncontiguous is easy to hide
        # bugs because .view(-1) will still work. So try to find a dim with size
        # > 1 and make that non-contiguous, i.e., stack + select on the
        # dimension directly after that.
        dim = ndim
        for d in range(ndim):
            if tensor.size(d) > 1:
                dim = d + 1
                break
        noncontig = torch.stack([torch.empty_like(tensor), tensor], dim).select(dim, 1).detach()
        if not (noncontig.numel() == 1 or noncontig.numel() == 0 or not noncontig.is_contiguous()):
            raise AssertionError(
                f"Expected noncontig to be non-contiguous or have numel <= 1, got numel={noncontig.numel()}"
            )
        noncontig.requires_grad = tensor.requires_grad
        return noncontig