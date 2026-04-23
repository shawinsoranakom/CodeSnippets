def assign_origin_node(result: Any, n: torch.fx.Node) -> None:
    # This is not complete, but it doesn't have to be: origin_node
    # tracking is best effort.  The logic here critically relies on direct
    # TensorBox -> StorageBox denoting a non-view; we don't bother trying
    # to get views to work.  Feel free to add any extra cases as needed.
    #
    # Note: we can't YOLO tree_map over this result, because if there are
    # buffers or a view involved, we might not be able to validly assign
    # the origin_node here.
    if isinstance(result, TensorBox) and isinstance(result.data, StorageBox):
        if isinstance(result.data.data, Loops):
            result.data.data._post_init_setattr("origin_node", n)
        elif isinstance(result.data.data, Buffer):
            result.data.data._post_init_setattr("origin_node", n)
            if isinstance(result.data.data, ComputedBuffer) and isinstance(
                result.data.data.data, Loops
            ):
                result.data.data.data._post_init_setattr("origin_node", n)
            # Not really multi-output, can straightforwardly recurse in
            elif (
                isinstance(result.data.data, MultiOutput)
                and not result.data.data.indices
            ):
                if isinstance(result.data.data.inputs[0], Buffer):
                    result.data.data.inputs[0]._post_init_setattr("origin_node", n)