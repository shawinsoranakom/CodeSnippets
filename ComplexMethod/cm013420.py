def _replace_attributes(gm: GraphModule, replacement: torch.nn.Module) -> None:
    gm.delete_all_unused_submodules()

    if isinstance(replacement, GraphModule):
        replacement.graph.lint()

    def try_get_attr(gm: torch.nn.Module, target: str) -> Any | None:
        module_path, _, attr_name = target.rpartition(".")
        try:
            mod: torch.nn.Module = gm.get_submodule(module_path)
        except AttributeError:
            return None
        attr = getattr(mod, attr_name, None)
        return attr

    for node in gm.graph.nodes:
        if node.op == "call_module" or node.op == "get_attr":
            gm_attr = try_get_attr(gm, node.target)
            replacement_attr = try_get_attr(replacement, node.target)

            # CASE 1: This target already exists as an attribute in our
            # result GraphModule. Whether or not it exists in
            # `replacement`, the existing submodule takes precedence.
            if gm_attr is not None:
                continue

            # CASE 2: The target exists as an attribute in `replacement`
            # only, so we need to copy it over.
            elif replacement_attr is not None:
                new_attr = copy.deepcopy(replacement_attr)
                if isinstance(replacement_attr, torch.nn.Module):
                    gm.add_submodule(node.target, new_attr)
                else:
                    setattr(gm, node.target, new_attr)

            # CASE 3: The target doesn't exist as an attribute in `gm`
            # or `replacement`
            else:
                raise RuntimeError(
                    'Attempted to create a "',
                    node.op,
                    '" node during subgraph rewriting '
                    f"with target {node.target}, but "
                    "the referenced attribute does not "
                    "exist in the replacement GraphModule",
                )

    gm.graph.lint()