def _get_notallclose_msg(
    analytical,
    numerical,
    output_idx,
    input_idx,
    complex_indices,
    test_imag=False,
    is_forward_ad=False,
) -> str:
    out_is_complex = (
        (not is_forward_ad) and complex_indices and output_idx in complex_indices
    )
    inp_is_complex = is_forward_ad and complex_indices and input_idx in complex_indices
    part = "imaginary" if test_imag else "real"
    element = "inputs" if is_forward_ad else "outputs"
    prefix = (
        ""
        if not (out_is_complex or inp_is_complex)
        else f"While considering the {part} part of complex {element} only, "
    )
    mode = "computed with forward mode " if is_forward_ad else ""
    return (
        prefix
        + f"Jacobian {mode}mismatch for output {output_idx:d} with respect to input {input_idx:d},\n"
        f"numerical:{numerical}\nanalytical:{analytical}\n"
    )