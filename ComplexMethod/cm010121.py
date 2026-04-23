def _vector_str(self, indent, summarize, formatter1, formatter2=None):
    # length includes spaces and comma between elements
    element_length = formatter1.width() + 2
    if formatter2 is not None:
        # width for imag_formatter + an extra j for complex
        element_length += formatter2.width() + 1

    elements_per_line = max(
        1, math.floor((PRINT_OPTS.linewidth - indent) / (element_length))
    )

    def _val_formatter(val, formatter1=formatter1, formatter2=formatter2):
        if formatter2 is not None:
            real_str = formatter1.format(val.real)
            imag_str = (formatter2.format(val.imag) + "j").lstrip()
            # handles negative numbers, +0.0, -0.0
            if imag_str[0] == "+" or imag_str[0] == "-":
                return real_str + imag_str
            else:
                return real_str + "+" + imag_str
        else:
            return formatter1.format(val)

    if self.dtype == torch.float4_e2m1fn_x2:  # type: ignore[attr-defined]
        # torch.float4_e2m1fn_x2 is special and does not support the casts necessary
        # to print it, we choose to display the uint8 representation here for
        # convenience of being able to print a tensor.
        # TODO(#146647): extend this to other dtypes without casts defined, such
        # as the bits, uint1..7 and int1..7 dtypes.
        self = self.view(torch.uint8)

    if summarize and not PRINT_OPTS.edgeitems:
        # Deal with edge case that negative zero is zero
        data = ["..."]
    elif summarize and self.size(0) > 2 * PRINT_OPTS.edgeitems:
        data = (
            [_val_formatter(val) for val in self[: PRINT_OPTS.edgeitems].tolist()]
            + [" ..."]
            + [_val_formatter(val) for val in self[-PRINT_OPTS.edgeitems :].tolist()]
        )
    else:
        data = [_val_formatter(val) for val in self.tolist()]

    data_lines = [
        data[i : i + elements_per_line] for i in range(0, len(data), elements_per_line)
    ]
    lines = [", ".join(line) for line in data_lines]
    return "[" + ("," + "\n" + " " * (indent + 1)).join(lines) + "]"