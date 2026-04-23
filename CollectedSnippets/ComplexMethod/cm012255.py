def remove_redundant_views(gm: torch.fx.GraphModule):
    """
    Removes redundant views by reusing existing ones.
    """
    with torch.utils._python_dispatch._disable_current_modes():
        # A dictionary mapping a tensor to all aliased views.
        views: dict[torch.fx.Node, dict[torch.dtype, torch.fx.Node]] = {}
        graph = gm.graph

        for node in graph.find_nodes(
            op="call_function", target=torch.ops.aten.view.dtype
        ):
            src = node.args[0]
            to_type = node.args[1]
            existing_views = views.get(src)
            is_needed = True

            if existing_views:
                # Replace the view with the an existing view if available.
                alias = existing_views.get(to_type)
                if alias:
                    is_needed = False
                    node.replace_all_uses_with(alias)
                    alias.meta.update(node.meta)
                    graph.erase_node(node)
            else:
                from_type = src.meta["val"].dtype
                existing_views = {from_type: src}
                views[src] = existing_views

            if is_needed:
                # Save the new alias but do not replace existing one.
                existing_views.setdefault(to_type, node)
                views[node] = existing_views

        # Clean up unused views.
        while True:
            unused_views = [alias for alias in views if not alias.users]
            if len(unused_views) == 0:
                break
            for unused in unused_views:
                views.pop(unused)
                graph.erase_node(unused)