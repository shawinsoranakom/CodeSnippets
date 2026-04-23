def forward_wrapper(self, *args, **kwargs):
        if any(
            isinstance(arg, torch.Tensor) and arg.dtype != target_dtype
            for arg in args
        ):
            args = [arg.to(target_dtype) if isinstance(arg, torch.Tensor) else arg for arg in args]
            kwargs = {k: v.to(target_dtype) if isinstance(v, torch.Tensor) else v for k, v in kwargs.items()}

        org_dtype = target_dtype
        for param in self.parameters():
            if param.dtype != target_dtype:
                org_dtype = param.dtype
                break

        if org_dtype != target_dtype:
            self.to(target_dtype)
        result = self.org_forward(*args, **kwargs)
        if org_dtype != target_dtype:
            self.to(org_dtype)

        if target_dtype != dtype_inference:
            if isinstance(result, tuple):
                result = tuple(
                    i.to(dtype_inference)
                    if isinstance(i, torch.Tensor)
                    else i
                    for i in result
                )
            elif isinstance(result, torch.Tensor):
                result = result.to(dtype_inference)
        return result