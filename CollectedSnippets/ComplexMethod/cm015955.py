def module_load(dest, src, assign=False):
        if isinstance(dest, cls):
            if assign:
                return src.detach()
            else:
                if type(src) is torch.Tensor:
                    return cls(src)
                elif type(src) is cls:
                    return src.detach()
                else:
                    if isinstance(src, MyWrapperLoadTensor):
                        return cls(src._data)
                    return cls(src)
        else:
            if not isinstance(src, cls):
                raise AssertionError(
                    f"Expected isinstance(src, {cls}) but got {type(src)}"
                )
            if not (
                type(dest) is torch.Tensor
                or type(dest) is torch.nn.Parameter
                or issubclass(cls, type(dest))
            ):
                raise AssertionError(
                    f"Expected dest to be Tensor, Parameter, or subclass of {cls}, got {type(dest)}"
                )
            if assign:
                return src.detach()
            else:
                if isinstance(src, MyWrapperLoadTensor):
                    if type(dest) not in {torch.Tensor, torch.nn.Parameter}:
                        return type(dest)(src._data)
                    else:
                        return src._data.detach()
                else:
                    return torch.Tensor(src)