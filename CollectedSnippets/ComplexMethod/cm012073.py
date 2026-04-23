def can_realize_as_comm_buffer(
    x: ir.TensorBox, comm_buffer_type: ir.CommBufferType
) -> bool:
    """
    Check if an input can be realized as a comm buffer of the specified
    `comm_buffer_type`.
    """
    data = _get_data(x)

    if isinstance(data, ir.Loops):
        return True

    # We cannot realize buffers as comm buffers if we don't control their
    # allocation.
    if isinstance(data, ir.Buffer) and not data.should_allocate():
        return False

    layout = data.get_output_spec()
    if isinstance(layout, ir.CommBufferLayout):
        return True

    if isinstance(layout, ir.FixedLayout):
        return True

    if isinstance(layout, ir.FlexibleLayout) and not is_symbolic(data.get_numel()):
        return True

    return False