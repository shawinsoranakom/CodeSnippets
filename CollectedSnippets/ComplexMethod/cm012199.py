def normalize_split_base(
    match: Match,
    _get_split_args: Callable[
        [torch.fx.Node], tuple[torch.fx.Node | None, Any | None, int | None]
    ],
):
    """
    Normalize split with split_size into split_with_sizes, so that we only deal with one type of split in
    subsequent optimizations
    """
    split_node = match.nodes[0]
    graph = match.graph
    split_input, split_size, split_dim = _get_split_args(split_node)
    if split_input is None or split_dim is None or split_size is None:
        log.debug("couldn't find split args")
        return
    if not is_node_meta_valid(split_node):
        log.debug("example value absent for node: %s", split_node)
        return
    assert isinstance(split_node.meta["example_value"], (list, tuple))
    split_sections = [t.size()[split_dim] for t in split_node.meta["example_value"]]

    if any(isinstance(section, torch.SymInt) for section in split_sections):
        # TODO dynamic_shapes with assume_static_by_default=False fails while AOT Autograd tracing.
        return
    if split_dim < 0:  # Normalize split dim
        split_dim += split_input.meta["example_value"].dim()

    new_args = (split_input, split_sections)
    new_kwargs = {"dim": split_dim}
    if (
        split_node.args == new_args
        and split_node.kwargs == new_kwargs
        and split_node.op == "call_function"
    ):
        return

    with graph.inserting_after(split_node):
        new_split_node = graph.call_function(
            torch.split,
            args=new_args,
            kwargs=new_kwargs,  # type: ignore[arg-type]
        )
    split_node.replace_all_uses_with(new_split_node)
    new_split_node.meta.update(split_node.meta)
    graph.erase_node(split_node)
    counters[backend]["normalization_pass"] += 1