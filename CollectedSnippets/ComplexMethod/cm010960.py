def log_abs_det_jacobian(self, x, y):
        if not (-x.dim() <= self.dim < x.dim()):
            raise AssertionError(
                f"dim {self.dim} out of range for x with {x.dim()} dimensions"
            )
        if x.size(self.dim) != self.length:
            raise AssertionError(
                f"x.size({self.dim}) = {x.size(self.dim)} must equal length {self.length}"
            )
        if not (-y.dim() <= self.dim < y.dim()):
            raise AssertionError(
                f"dim {self.dim} out of range for y with {y.dim()} dimensions"
            )
        if y.size(self.dim) != self.length:
            raise AssertionError(
                f"y.size({self.dim}) = {y.size(self.dim)} must equal length {self.length}"
            )
        logdetjacs = []
        start = 0
        for trans, length in zip(self.transforms, self.lengths):
            xslice = x.narrow(self.dim, start, length)
            yslice = y.narrow(self.dim, start, length)
            logdetjac = trans.log_abs_det_jacobian(xslice, yslice)
            if trans.event_dim < self.event_dim:
                logdetjac = _sum_rightmost(logdetjac, self.event_dim - trans.event_dim)
            logdetjacs.append(logdetjac)
            start = start + length  # avoid += for jit compat
        # Decide whether to concatenate or sum.
        dim = self.dim
        if dim >= 0:
            dim = dim - x.dim()
        dim = dim + self.event_dim
        if dim < 0:
            return torch.cat(logdetjacs, dim=dim)
        else:
            return sum(logdetjacs)