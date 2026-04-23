def _is_valid_return_type(match: TypeHintMatch, node: nodes.NodeNG) -> bool:
    if _is_valid_type(match.return_type, node, True):
        return True

    if isinstance(node, nodes.BinOp):
        return _is_valid_return_type(match, node.left) and _is_valid_return_type(
            match, node.right
        )

    if isinstance(match.return_type, (str, list)) and isinstance(node, nodes.Name):
        if isinstance(match.return_type, str):
            valid_types = {match.return_type}
        else:
            valid_types = {el for el in match.return_type if isinstance(el, str)}
        if "Mapping[str, Any]" in valid_types:
            valid_types.add("TypedDict")

        try:
            for infer_node in node.infer():
                if _check_ancestry(infer_node, valid_types):
                    return True
        except NameInferenceError:
            for class_node in node.root().nodes_of_class(nodes.ClassDef):
                if class_node.name != node.name:
                    continue
                for infer_node in class_node.infer():
                    if _check_ancestry(infer_node, valid_types):
                        return True

    return False