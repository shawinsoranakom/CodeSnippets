def _format_tensor(t, indent_level=0, sci_mode=None):
    """Format torch's tensor in a pretty way to be shown 👀 in the test report."""

    # `torch.testing.assert_close` could accept python int/float numbers.
    if not isinstance(t, torch.Tensor):
        t = torch.tensor(t)

    # Simply make the processing below simpler (not to handle both cases)
    is_scalar = False
    if t.ndim == 0:
        t = torch.tensor([t])
        is_scalar = True

    # For scalar or one-dimensional tensor, keep it as one-line. If there is only one element along any dimension except
    # the last one, we also keep it as one-line.
    if t.ndim <= 1 or set(t.shape[0:-1]) == {1}:
        # Use `detach` to remove `grad_fn=<...>`, and use `to("cpu")` to remove `device='...'`
        t = t.detach().to("cpu")

        # We work directly with the string representation instead the tensor itself
        t_str = str(t)

        # remove `tensor( ... )` so keep only the content
        t_str = t_str.replace("tensor(", "").replace(")", "")

        # Sometimes there are extra spaces between `[` and the first digit of the first value (for alignment).
        # For example `[[ 0.06, -0.51], [-0.76, -0.49]]`. It may have multiple consecutive spaces.
        # Let's remove such extra spaces.
        while "[ " in t_str:
            t_str = t_str.replace("[ ", "[")

        # Put everything in a single line. We replace `\n` by a space ` ` so we still keep `,\n` as `, `.
        t_str = t_str.replace("\n", " ")

        # Remove repeated spaces (introduced by the previous step)
        while "  " in t_str:
            t_str = t_str.replace("  ", " ")

        # remove leading `[` and `]` for scalar tensor
        if is_scalar:
            t_str = t_str[1:-1]

        t_str = " " * 4 * indent_level + t_str

        return t_str

    # Otherwise, we separate the representations of each element along an outer dimension by new lines (after a `,`).
    # The representation of each element is obtained by calling this function recursively with current `indent_level`.
    else:
        t_str = str(t)

        # (For the recursive calls should receive this value)
        if sci_mode is None:
            sci_mode = "e+" in t_str or "e-" in t_str

        # Use the original content to determine the scientific mode to use. This is required as the representation of
        # t[index] (computed below) maybe have different format regarding scientific notation.
        torch.set_printoptions(sci_mode=sci_mode)

        t_str = " " * 4 * indent_level + "[\n"
        # Keep the ending `,` for all outer dimensions whose representations are not put in one-line, even if there is
        # only one element along that dimension.
        t_str += ",\n".join(_format_tensor(x, indent_level=indent_level + 1, sci_mode=sci_mode) for x in t)
        t_str += ",\n" + " " * 4 * indent_level + "]"

        torch.set_printoptions(sci_mode=None)

    return t_str