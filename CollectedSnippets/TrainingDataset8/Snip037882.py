def _maybe_compose_deltas(old_delta: Delta, new_delta: Delta) -> Optional[Delta]:
    """Combines new_delta onto old_delta if possible.

    If the combination takes place, the function returns a new Delta that
    should replace old_delta in the queue.

    If the new_delta is incompatible with old_delta, the function returns None.
    In this case, the new_delta should just be appended to the queue as normal.
    """
    old_delta_type = old_delta.WhichOneof("type")
    if old_delta_type == "add_block":
        # We never replace add_block deltas, because blocks can have
        # other dependent deltas later in the queue. For example:
        #
        #   placeholder = st.empty()
        #   placeholder.columns(1)
        #   placeholder.empty()
        #
        # The call to "placeholder.columns(1)" creates two blocks, a parent
        # container with delta_path (0, 0), and a column child with
        # delta_path (0, 0, 0). If the final "placeholder.empty()" Delta
        # is composed with the parent container Delta, the frontend will
        # throw an error when it tries to add that column child to what is
        # now just an element, and not a block.
        return None

    new_delta_type = new_delta.WhichOneof("type")
    if new_delta_type == "new_element":
        return new_delta

    if new_delta_type == "add_block":
        return new_delta

    return None