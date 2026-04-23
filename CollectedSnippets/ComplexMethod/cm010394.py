def identify_triton_stores_from_ast(tree: ast.Module) -> TritonStores:
    stores = []

    def _extract_arg(node, arg_name, positional_index):
        """
        Extract an argument from a Call node, checking both positional and keyword args.
        Returns the AST node for the argument, or None if not found.
        """
        # Check positional args first
        if len(node.args) > positional_index:
            return node.args[positional_index]

        # Check keyword args
        for keyword in node.keywords:
            if keyword.arg == arg_name:
                return keyword.value

        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if this is a tl.store call
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "tl"
                and node.func.attr == "store"
            ):
                # Extract required arguments
                pointer_node = _extract_arg(node, "pointer", 0)
                value_node = _extract_arg(node, "value", 1)

                if pointer_node is None or value_node is None:
                    continue

                stores.append(TritonStore(node, pointer_node, value_node))

    return TritonStores(stores=stores)