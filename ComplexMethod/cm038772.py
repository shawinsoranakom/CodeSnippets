def event_arg_repr(arg) -> str:
    if arg is None or type(arg) in [float, int, bool, str]:
        return f"{arg}"
    elif isinstance(arg, list):
        return f"[{', '.join([event_arg_repr(x) for x in arg])}]"
    elif isinstance(arg, tuple):
        return f"({', '.join([event_arg_repr(x) for x in arg])})"
    else:
        assert isinstance(arg, _TensorMetadata), f"Unsupported type: {type(arg)}"
        sizes_str = ", ".join([str(x) for x in arg.sizes])
        return f"{str(arg.dtype).replace('torch.', '')}[{sizes_str}]"