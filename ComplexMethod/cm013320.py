def wrapper(x: npt.NDArray, *args, **kwargs):
        # Copy keys into a set
        keys = set(kwargs.keys())

        dim = kwargs.pop("dim", None)
        keepdim = kwargs.pop("keepdim", False)

        if "dim" in keys:
            dim = tuple(dim) if isinstance(dim, Sequence) else dim

            # NumPy reductions don't accept dim=0 for scalar inputs
            # so we convert it to None if and only if dim is equivalent
            if x.ndim == 0 and dim in {0, -1, (0,), (-1,)}:
                kwargs["axis"] = None
            else:
                kwargs["axis"] = dim

        if "keepdim" in keys and supports_keepdims:
            kwargs["keepdims"] = keepdim

        if "mask" in keys:
            mask = kwargs.pop("mask")
            if mask is not None:
                if mask.layout != torch.strided:
                    raise AssertionError(
                        f"Expected mask.layout == torch.strided, got {mask.layout}"
                    )
                kwargs["where"] = mask.cpu().numpy()

        if "identity" in keys:
            identity = kwargs.pop("identity")
            if identity is not None:
                if identity.dtype is torch.bfloat16:
                    identity = identity.cpu().to(torch.float32)
                else:
                    identity = identity.cpu()
                kwargs["initial"] = identity.numpy()

        result = f(x, *args, **kwargs)

        # Unsqueeze reduced dimensions if NumPy does not support keepdims
        if keepdim and not supports_keepdims and x.ndim > 0:
            dim = list(range(x.ndim)) if dim is None else dim
            result = np.expand_dims(result, dim)

        return result