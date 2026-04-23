def inner(*args: _P.args, **kwargs: _P.kwargs) -> Any:
            with torch.no_grad():
                outs = orig_fwd(*args, **kwargs)

            # Handle the case where if the input is passed on directly to the output, we call view_as
            # Refer to https://github.com/pytorch/pytorch/blob/main/torch/csrc/autograd/custom_function.cpp#L254
            tensor_args = {arg for arg in args if isinstance(arg, torch.Tensor)}
            if isinstance(outs, torch.Tensor):
                if outs in tensor_args:
                    return outs.view_as(outs)
                else:
                    return outs

            new_outs = []
            for out in outs:
                if isinstance(out, torch.Tensor):
                    if out in tensor_args:
                        new_outs.append(out.view_as(out))
                    else:
                        new_outs.append(out)
                else:
                    new_outs.append(out)
            return tuple(new_outs)