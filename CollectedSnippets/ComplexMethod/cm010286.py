def _normalize_nn_module_stack(gm_torch_level, root_cls):
    # Append a root module to every nn_module_stack.
    root = "L['self']"
    root_key = re.sub(r"[^a-zA-Z0-9]", "_", root)
    for gm in gm_torch_level.modules():
        if not isinstance(gm, torch.fx.GraphModule):
            continue
        for node in gm.graph.nodes:
            if node.op in ["placeholder", "output"]:
                continue
            add_root = True
            if nn_module_stack := node.meta.get("nn_module_stack", {}):
                path, ty = next(iter(nn_module_stack.values()))
                # After deserializing the class `ty` might not exist anymore so
                # it could be a string
                if inspect.isclass(ty) and issubclass(ty, torch.nn.Module):
                    # TODO Figure out why sometimes we have root sometimes we don't.
                    if path == root and ty is root_cls:
                        add_root = False
                else:
                    if not isinstance(ty, str):
                        raise AssertionError(f"expected ty to be str, got {type(ty)}")
            if add_root:

                def normalize_path(path):
                    if path == "L['self']":
                        return ""
                    if path.startswith("L['self']."):
                        return path[len("L['self'].") :]
                    return path

                nn_module_stack = {
                    root_key: (root, root_cls.__module__ + "." + root_cls.__qualname__),
                    # pyrefly: ignore [unbound-name]
                    **nn_module_stack,
                }
                node.meta["nn_module_stack"] = {
                    key: (normalize_path(path), ty)
                    for key, (path, ty) in nn_module_stack.items()
                }