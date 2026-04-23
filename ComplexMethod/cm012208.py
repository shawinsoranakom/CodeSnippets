def normalize_split_default_aten(match: Match, *args, **kwargs):
    split_node = match.nodes[0]
    graph = match.graph
    split_input, split_size, split_dim = _get_split_args_default(split_node)
    if split_input is None or split_dim is None or split_size is None:
        log.debug("couldn't find split args")
        return
    if not is_node_meta_valid(split_node):
        log.debug("val absent for node: %s", split_node)
        return
    assert isinstance(split_node.meta["val"], (list, tuple))
    split_sections = [t.size()[split_dim] for t in split_node.meta["val"]]
    if any(isinstance(section, torch.SymInt) for section in split_sections):
        # TODO dynamic_shapes with assume_static_by_default=False fails while AOT Autograd tracing.
        return
    if split_dim < 0:  # Normalize split dim
        split_dim += split_input.meta["val"].dim()
    # we also need to check the input of the split_node
    # primals =torch.randn(4096, 300)
    # split = torch.ops.aten.split.Tensor(primals, 320, 1) -> truncate to 300 automatically
    # split_2 = torch.ops.aten.split_with_sizes.default(primals, [320], dim = 1) -> runtime error
    split_input_size = split_input.meta["val"].shape[split_dim]
    split_size = min(split_size, split_input_size)
    split_section_list = [split_size] * (len(split_node.meta["val"]))
    new_args = (split_input, split_section_list)
    new_kwargs = {"dim": split_dim}
    if (
        split_node.args == new_args
        and split_node.kwargs == new_kwargs
        and split_node.op == "call_function"
    ):
        return

    with graph.inserting_after(split_node):
        new_split_node = graph.call_function(
            torch.ops.aten.split_with_sizes.default,
            args=new_args,
            kwargs=new_kwargs,  # type: ignore[arg-type]
        )
    split_node.replace_all_uses_with(new_split_node)
    new_split_node.meta.update(split_node.meta)
    graph.erase_node(split_node)
    counters[backend]["normalization_aten_pass"] += 1