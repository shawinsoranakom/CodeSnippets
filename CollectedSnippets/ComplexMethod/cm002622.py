def recursive_look_for_imports(node):
        if isinstance(node, ast.Try):
            return  # Don't recurse into Try blocks and ignore imports in them
        elif isinstance(node, ast.If):
            test = node.test
            for condition_node in ast.walk(test):
                if isinstance(condition_node, ast.Call):
                    check_function = getattr(condition_node.func, "id", "")
                    if (
                        check_function.endswith("available")
                        and check_function.startswith("is_flash_attn")
                        or hasattr(transformers.utils.import_utils, check_function)
                    ):
                        # Don't recurse into "if flash_attn_available()" or any "if library_available" blocks
                        # that appears in `transformers.utils.import_utils` and ignore imports in them
                        return
        elif isinstance(node, ast.Import):
            # Handle 'import x' statements
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                if top_module:
                    imported_modules.add(top_module)
        elif isinstance(node, ast.ImportFrom):
            # Handle 'from x import y' statements, ignoring relative imports
            if node.level == 0 and node.module:
                top_module = node.module.split(".")[0]
                if top_module:
                    imported_modules.add(top_module)

        # Recursively visit all children
        for child in ast.iter_child_nodes(node):
            recursive_look_for_imports(child)