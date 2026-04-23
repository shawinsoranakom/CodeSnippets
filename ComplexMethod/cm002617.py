def prune_intermediate_layers(node):
    """
    Recursively removes intermediate layers from the tree to improve readability.
    Keeps at least the first and last layers if many consecutive layers are present.

    Args:
        node (`dict`): The root or subnode to prune recursively.
    """
    if not node.get("children"):
        return
    layer_blocks = [(i, child) for i, child in enumerate(node["children"]) if is_layer_block(child)]

    if len(layer_blocks) > 2:
        to_remove = [i for i, _ in layer_blocks[1:-1]]
        node["children"] = [child for i, child in enumerate(node["children"]) if i not in to_remove]

    for child in node["children"]:
        prune_intermediate_layers(child)