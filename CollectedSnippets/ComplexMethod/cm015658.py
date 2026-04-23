def __torch_function__(cls, func, types, args=(), kwargs=None):
                if kwargs is None:
                    kwargs = {}

                result = super().__torch_function__(func, types, args, kwargs)

                quant_type = None
                for arg in args:
                    if isinstance(arg, list) and isinstance(arg[0], GGUFParameter):
                        quant_type = arg[0].quant_type
                        break
                    if isinstance(arg, GGUFParameter):
                        quant_type = arg.quant_type
                        break
                if isinstance(result, torch.Tensor):
                    return cls(result, quant_type=quant_type)
                # Handle tuples and lists
                elif isinstance(result, (tuple, list)):
                    # Preserve the original type (tuple or list)
                    wrapped = [
                        (
                            cls(x, quant_type=quant_type)
                            if isinstance(x, torch.Tensor)
                            else x
                        )
                        for x in result
                    ]
                    return type(result)(wrapped)
                else:
                    return result