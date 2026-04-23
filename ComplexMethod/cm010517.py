def split_complex_arg(
    arg: Tensor | ComplexTensor | complex | Number,
) -> tuple[Tensor, Tensor] | tuple[Number, Number]:
    """
    Split a complex argument into a real/imaginary component.

    If real, use zero for the imaginary part.
    """
    if isinstance(arg, ComplexTensor):
        return split_complex_tensor(arg)
    if isinstance(arg, Tensor):
        if is_complex(arg):
            return arg.real, arg.imag
        return arg, torch.zeros_like(arg)
    # TODO (hameerabbasi): Should there be a `torch.SymComplex`?
    if isinstance(arg, complex):
        return arg.real, arg.imag
    if isinstance(arg, float | torch.SymFloat):
        return arg, 0.0
    if isinstance(arg, int | torch.SymInt):
        return arg, 0
    if isinstance(arg, bool | torch.SymBool):
        return arg, False
    raise TypeError(f"Expected tensor or number got, {type(arg)}")